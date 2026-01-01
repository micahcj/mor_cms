<script lang="ts">
	import ListRenderer from '$lib/Components/ListRenderer.svelte';
	import ListRenderer2 from '$lib/Components/ListRenderer2.svelte';
	import TextButton from '$lib/Components/TextButton.svelte';
	import {
		indentValues,
		serializeContent,
		type IndentValue,
		type TextObject
	} from '$lib/static_resources';
	import { exportListHtml } from '$lib/utilities';
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
		// console.log('state changed');
		// console.log($state.snapshot(textObjs));
		console.log('serialized effect', serializeContent(textObjs));
	});
	$effect(() => {
		resultText = serializeContent(textObjs);
		if (listEle) {
			console.log(listEle.innerHTML);
		}
		console.log(nodes());
	});

	function dlJson() {
		const data = JSON.stringify({ json: resultText, html: exportListHtml(nodes()) });
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

	function editText(id: string, value: string) {
		textObjs = textObjs.map((o) => (o.id === id ? { ...o, text: value } : o));
	}

	function indent(id: string) {
		textObjs = indentTextObject(textObjs, id);
	}

	function outdent(id: string) {
		textObjs = outdentTextObject(textObjs, id);
	}

	onMount(() => {
		for (const i in nodes) {
			console.log(i, 'node,', nodes[i]);
		}
	});
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>

<ul
	class="content"
	onchange={() => {
		console.log($state.snapshot(textObjs));
		console.log('serialized', serializeContent(textObjs));
	}}
>
	{#each textObjs as obj, i (obj.id)}
		<div class="textbutton-container">
			<div class="plus-minus">
				<button onclick={() => addTextObj(i)}>+</button>
				<button onclick={() => removeTextObj(i)}>-</button>
			</div>
			<TextButton bind:text={textObjs[i].text} bind:indentValue={textObjs[i].indentValue} />
		</div>
	{/each}
</ul>
<div class="result-text">
	<h3>Result Text:</h3>
	<ul class="listEle" bind:this={listEle}>
		{#each resultText as item, i (i)}
			{#if Array.isArray(item)}
				<ul>
					{#each item as sub}
						<li>{sub}</li>
					{/each}
				</ul>
			{:else}
				<li class="solo">{item}</li>
			{/if}
		{/each}
	</ul>
	<p>{JSON.stringify(resultText)}</p>
	{#if listEle}
		<p>{listEle.innerHTML}</p>
		<p>{listEle.outerHTML}</p>
	{/if}
	<button onclick={dlJson}>Save JSON</button>
</div>
<ListRenderer nodes={textObjs}></ListRenderer>

<ListRenderer2 {nodes} onEdit={editText} onIndent={indent} onOutdent={outdent} />
<pre>{exportListHtml(nodes())}</pre>

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
