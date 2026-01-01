<script lang="ts">
	import ListRenderer from '$lib/Components/ListRenderer.svelte';
	import ListRenderer2 from '$lib/Components/ListRenderer2.svelte';
	import TextButton from '$lib/Components/TextButton.svelte';
	import {
		indentValues,
		serializeContent,
		type IndentValue,
		type TextObject
	} from '$lib/static_resources2';
	// import { exportListHtml } from '$lib/utilities2';
	import {
		indentNode,
		outdentNode,
		reorderNode,
		textObjectsToTree,
		treeToTextObjects,
		exportListHtmlPretty,
		exportListHtmlWithClasses,
		makeChildOf
	} from '$lib/utiltities2';
	import { onMount } from 'svelte';

	const defaultTextObj: TextObject = { text: 'default', indentValue: 'Main' };
	let resultText: Array<string | string[]> = $state([]);
	// let resultText: Array<string | string[]> = $state([]);=  $derived(() => serializeContent(textObjs)); // = $state([]);
	let textObjs: TextObject[] = $state([
		{ text: 'shid1', indentValue: 'Main', id: crypto.randomUUID() },
		{ text: 'shid2', indentValue: 'Main', id: crypto.randomUUID() }
	]);
	let listEle: HTMLUListElement = $state();
	let nodes: Node[] = $derived(() => serializeContent(textObjs));

	function createTextObj(): TextObject {
		return { ...defaultTextObj, id: crypto.randomUUID() };
	}

	function addTextObj(index: number) {
		const insertIndex = index + 1;

		textObjs = [...textObjs.slice(0, insertIndex), createTextObj(), ...textObjs.slice(insertIndex)];
	}
	function removeTextObj(index: number) {
		if (textObjs.length <= 1) {
			return;
		}
		textObjs = [...textObjs.slice(0, index), ...textObjs.slice(index + 1)];
	}

	$effect(() => {
		resultText = serializeContent(textObjs);
	});

	function dlJson() {
		const data = JSON.stringify({
			json: resultText,
			html: exportListHtmlPretty(treeNodes, false),
			styledHtml: exportListHtmlWithClasses(treeNodes, false)
		});
		const dlEle = document.createElement('a');
		dlEle.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(data));
		dlEle.setAttribute('download', 'resultText.json');
		dlEle.click();
	}
	export function indentTextObject(list: TextObject[], id: string) {
		return list.map((o) =>
			o.id === id && o.indentValue === 'Main' ? { ...o, indentValue: 'Bullet' } : o
		);
	}

	export function outdentTextObject(list: TextObject[], id: string) {
		return list.map((o) =>
			o.id === id && o.indentValue !== 'Main' ? { ...o, indentValue: 'Main' } : o
		);
	}

	let treeNodes = $derived(textObjectsToTree(textObjs));

	// Update handlers to convert back to TextObject format
	function reorder(fromId: string, toId: string, position: 'before' | 'after') {
		const result = reorderNode($state.snapshot(treeNodes), fromId, toId, position);
		if (result) {
			textObjs = treeToTextObjects(result.tree);
		}
	}

	function indent(id: string) {
		const result = indentNode($state.snapshot(treeNodes), id);
		if (result) {
			textObjs = treeToTextObjects(result.tree);
		}
	}

	function outdent(id: string) {
		const result = outdentNode($state.snapshot(treeNodes), id);
		if (result) {
			textObjs = treeToTextObjects(result.tree);
		}
	}

	function editText(id: string, value: string) {
		textObjs = textObjs.map((o) => (o.id === id ? { ...o, text: value } : o));
	}

	function makeChild(childId: string, parentId: string) {
		const result = makeChildOf($state.snapshot(treeNodes), childId, parentId);
		if (result) {
			textObjs = treeToTextObjects(result.tree);
		}
	}

	onMount(() => {
		for (const i in nodes) {
			console.log(i, 'node,', nodes[i]);
		}
	});
</script>

<div class="result-text">
	<h3>Result Text:</h3>
	<div>{@html exportListHtmlPretty(treeNodes)}</div>
	<button onclick={dlJson}>Save JSON</button>
</div>
<p>List ListRenderer2</p>
<ListRenderer2
	nodes={treeNodes}
	onEdit={editText}
	onIndent={indent}
	onOutdent={outdent}
	onReorder={reorder}
	onMakeChild={makeChild}
/>

<pre>{exportListHtmlPretty(treeNodes)}</pre>

<style>
	.plus-minus {
		display: flex;
		flex-direction: column;

		/* width: 1rem; */
		button {
			display: flex;
			aspect-ratio: 1/1;
			width: 1rem;
			align-items: center;
			justify-content: center;
			border-radius: 40%;
			border: 1px solid black;
		}
	}

	.textbutton-container {
		display: flex;
		gap: 1rem;
		/* margin: auto; */
		align-items: center;
	}

	.content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
		justify-content: left;
	}

	.result-text {
		display: flex;
		flex-direction: column;
		font-family:
			'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana,
			sans-serif;
	}
	.result-text .solo {
		gap: 0;
		list-style: none;
	}
</style>
