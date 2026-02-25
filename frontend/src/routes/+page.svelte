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
		makeChildOf,
		aggregateReport
	} from '$lib/utiltities2';
	import { onMount } from 'svelte';
	import { v4 as uuid } from 'uuid';

	let graphs = $state(1);
	const defaultTextObj: TextObject = { text: 'default', indentValue: 'Main' };
	let resultText: Array<string | string[]> = $state([]);
	// let resultText: Array<string | string[]> = $state([]);=  $derived(() => serializeContent(textObjs)); // = $state([]);
	const exObjs = [
		{ text: 'shid1', indentValue: 'Main', id: uuid() },
		{ text: 'shid2', indentValue: 'Main', id: uuid() }
	];
	let textObjs: TextObject[] = $state([...exObjs]);
	let listEle: HTMLUListElement = $state();
	let nodes: Node[] = $derived(() => serializeContent(textObjs));
	let sheets: Array<string | number> = $state([]);
	let year: number = $state(2026);
	let files: File[] = [];

	function createTextObj(): TextObject {
		return { ...defaultTextObj, id: uuid() };
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

	async function reloadChart() {
		await fetch('http://localhost:7001/api/reload_barchart', { method: 'POST' });
	}

	async function sendData() {
		const url = new URL('http://localhost:7001/api/highlights');
		const data = {
			nodes: treeNodes,
			objects: textObjs,
			html: exportListHtmlPretty(treeNodes, false),
			prettyHTML: exportListHtmlWithClasses(treeNodes, false)
		};
		const response = await fetch(url, { method: 'POST', body: JSON.stringify(data) });
		const result = await response.json();
		console.log('sendData result:', result);
	}

	async function requestReport(dept: string = 'PrimaryCare', download = true) {
		console.log('requestReport');
		const response = await aggregateReport(dept);
		// for (const path of paths) {
		console.log(response, download);
		if (download) {
			const dl = document.createElement('a');
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			console.log(url);
			dl.href = url;
			dl.click();
			dl.remove();
			URL.revokeObjectURL(url);
		}
	}

	async function selectWorkbook(year: 2024 | 2025 | 2026) {
		const url = new URL('http://localhost:7001/api/load_sheet');
		const body = { year };
		const response = await fetch(url, {
			method: 'POST',
			body: JSON.stringify(body),
			headers: { 'Content-Type': 'application/json' }
		});
		console.log(body, JSON.stringify(body));
		const sheetNames = await response.json();
		console.log(sheetNames);
		sheets = sheetNames;
		return sheetNames;
	}

	async function sendWorkbook() {
		const url = new URL('http://localhost:7001/api/upload_wb');
		if (files) {
			const formData = new FormData();
			formData.append('file', files[0]);
			const response = await fetch(url, {
				method: 'POST',
				body: formData
				// headers: { 'Content-Type': files[0].type }
			});
			const result = await response.json();
			console.log(result);
		} else {
			console.log('no files');
		}
	}

	onMount(async () => {
		for (const i in nodes) {
			console.log(i, 'node,', nodes[i]);
		}
		try {
			await selectWorkbook(year);
		} catch (error) {
			console.log(error);
		}
	});
</script>

<div class="container">
	<div class="box">
		<div class="result-text">
			<h3>Result Text:</h3>
			<div>{@html exportListHtmlPretty(treeNodes)}</div>
			<button onclick={dlJson}>Save JSON</button>
			<button onclick={sendData}>Send JSON</button>
			<button onclick={reloadChart}>Reload Barchart</button>
			<button onclick={() => requestReport()}>PrimaryCare Report</button>
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
	</div>
	<div class="box">
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
	</div>
	<div>
		<form
			onsubmit={(e) => {
				e.preventDefault();
			}}
		>
			<p>Graphs: {graphs}</p>
			<input type="radio" id="graphs-1" name="graph-option" onclick={() => (graphs = 1)} />
			<label for="graphs-1">1</label>

			<input type="radio" id="graphs-2" name="graph-option" onclick={() => (graphs = 2)} />
			<label for="graphs-2">2</label>
		</form>
	</div>
	<div class="mor-page box">
		<div class="heading">
			<img class="logo" src="/src/public/static/logo.jpg" />
			<div class="title">
				<p>Ochsner Refill Center</p>
				<p>Operational Report</p>
			</div>
			<div class="datebox">
				<div class="date">
					<p>Date:</p>
					<p>MONTH YEAR</p>
				</div>
			</div>
		</div>

		{#if graphs == 1}
			<div class="one-graph">
				<img class="graph" src="/src/public/content/tableau_bar.svg" />
			</div>
		{:else}
			<div class="graphs">
				<img class="graph" src="/src/public/content/donut.svg" />
				<img class="graph" src="/src/public/content//donut.svg" />
			</div>{/if}
		<div class="metrics-box">
			<div>
				<p class="text-heading">Metrics</p>
			</div>
			<div class="compressed-text">
				<p>
					Medication refills addressed -
					<b> 46,474 </b>
				</p>
				<p>
					Percentage of encounters with 24H Turnaround Time -
					<b> 93.7% </b>
				</p>
				<p>
					Percentage of refills handled by Refill Center -
					<b> 66.8% </b>
				</p>
			</div>
		</div>
		<div>
			<div>
				<p class="text-heading">Highlights``</p>
			</div>
			{@html exportListHtmlPretty(treeNodes)}
		</div>
	</div>
</div>
<div>
	<select bind:value={year} onchange={() => selectWorkbook(year)}>
		{#each [2024, 2025, 2026] as year (year)}
			<option value={year}>{year}</option>
		{/each}
	</select>
	<p>{sheets}</p>
</div>
<div>
	<label for="template"> HTML Template </label>
	<input type="file" id="template" bind:files />
	<button onclick={sendWorkbook}>Upload</button>
</div>
<div><pre>{exportListHtmlPretty(treeNodes)}</pre></div>

<style>
	.mor-page {
		display: flex;
		flex-direction: column;
		width: 100%;
	}

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

	.footer-container .text-heading,
	.footer-container .foot-text {
		font-size: x-small;
		margin: 0;
	}

	.compressed-text {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		column-gap: 0.5rem;
		grid-auto-flow: column;
		font-size: small;
		margin: auto;
		text-align: center;
	}

	.text-heading {
		color: #13477d;
		font-weight: 700;
		margin: 0;
		font-size: 1.3rem;
	}
	.container {
		display: grid;
		grid-template-columns: repeat(2, fr);
		grid-template-rows: auto;
	}
	/* .container > div {
		flex: 50%;
	} */
	.box {
		border: 2px solid black;
		margin: auto;
		padding: 1rem;
	}

	.heading {
		display: inline-flex;
		column-gap: 5rem;
		font-size: medium;
		height: min-content;
		width: auto;
		margin: auto;
	}

	.logo {
		height: 100px;
		width: 100px;
		margin: auto 0;
	}

	.title {
		text-align: center;
		margin: auto;
		font-weight: bold;
	}

	.date {
		display: flex;
		flex-direction: column;
		justify-content: right;
		font-size: small;
		row-gap: 5px;
		width: 100px;
		break-after: always;
	}

	.date p {
		display: flex;
		margin: 0;
		justify-content: right;
	}

	.graphs {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		justify-content: center;
		margin: 0 auto;
		column-gap: 10px;
		width: 90%;
		height: auto;
		/* max-height: 5rem; */
	}
	.one-graph {
		display: grid;
		grid-template-columns: repeat(1, 1fr);
		justify-content: center;
		margin: 0 auto;
		column-gap: 10px;
		max-width: 90%;
		/* height: auto; */
		/* max-height: 5rem; */
	}

	.graph {
		display: flex;
		/* height: 250px; */
		width: 100%;
		height: 100%;
		max-height: 15rem;
	}

	pre {
		/* font-family:
			'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana,
			sans-serif; */
		grid-column: span 2;
		display: flex;
		margin: auto;
		min-width: 10rem;
		width: fit-content;
	}
</style>
