<script lang="ts">
	import type { TextObject, TreeNode } from '$lib/static_resources2';
	import ListRenderer from './ListRenderer2.svelte';
	import {
		findNode,
		indentNode,
		outdentNode,
		moveNodeById,
		canIndent,
		canOutdent
	} from '$lib/utiltities2';

	interface Props {
		nodes: TreeNode[];
	}
	let { nodes }: Props = $props();

	let selectedId = $state<string | null>(null);
	let dragFromId = $state<string | null>(null);
	let dragIntent: 'indent' | 'outdent' | null = $state(null);
	let startX = 0;

	/* --------------------------
	   KEYBOARD HANDLING
	--------------------------- */
	function handleKey(e: KeyboardEvent) {
		if (!selectedId) return;

		switch (true) {
			case e.key === 'Tab':
				e.preventDefault();
				if (e.shiftKey && canOutdent($state.snapshot(nodes), selectedId)) {
					const mutation = outdentNode($state.snapshot(nodes), selectedId);
					if (mutation) nodes = mutation.tree;
				} else if (!e.shiftKey && canIndent($state.snapshot(nodes), selectedId)) {
					const mutation = indentNode($state.snapshot(nodes), selectedId);
					if (mutation) nodes = mutation.tree;
				}
				break;

			case (e.ctrlKey || e.metaKey) && e.key === 'ArrowUp':
				e.preventDefault();
				moveRelative(-1);
				break;

			case (e.ctrlKey || e.metaKey) && e.key === 'ArrowDown':
				e.preventDefault();
				moveRelative(1);
				break;
		}
	}

	function moveRelative(dir: -1 | 1) {
		const found = findNode($state.snapshot(nodes), selectedId!);
		if (!found) return;

		const container = found.parent?.children ?? nodes;
		const target = container[found.index + dir];
		if (!target) return;

		const mutation = moveNodeById(
			$state.snapshot(nodes),
			selectedId!,
			target.id,
			dir === -1 ? 'before' : 'after'
		);
		if (mutation) nodes = mutation.tree;
	}

	/* --------------------------
	   DRAG HANDLING
	--------------------------- */
	function onDragOver(event: MouseEvent) {
		event.preventDefault();
		if (!dragFromId) return;

		const dx = event.clientX - startX;
		dragIntent = dx > 24 ? 'indent' : dx < -24 ? 'outdent' : null;
	}

	function onDrop() {
		if (!dragFromId || !dragIntent) return;

		applyDragMutation(dragFromId, dragIntent);
		dragFromId = dragIntent = null;
	}

	function applyDragMutation(id: string, intent: 'indent' | 'outdent') {
		nodes = intent === 'indent' ? indentTextObject(nodes, id) : outdentTextObject(nodes, id);
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

	// function onDrop() {
	// 	if (!dragFromId) return;

	// 	if (dragIntent === 'indent' && canIndent($state.snapshot(nodes), dragFromId)) {
	// 		const mutation = indentNode($state.snapshot(nodes), dragFromId);
	// 		if (mutation) nodes = mutation.tree;
	// 	}

	// 	if (dragIntent === 'outdent' && canOutdent($state.snapshot(nodes), dragFromId)) {
	// 		const mutation = outdentNode($state.snapshot(nodes), dragFromId);
	// 		if (mutation) nodes = mutation.tree;
	// 	}

	// 	dragFromId = dragIntent = null;
	// }

	function updateText(id: string, value: string) {
		nodes = nodes.map((o) => (o.id === id ? { ...o, text: value } : o));
	}
</script>

<div tabindex="0" onkeydown={handleKey}>
	<ul>
		{#each nodes as node (node.id)}
			<li
				draggable
				tabindex="0"
				class:selected={selectedId === node.id}
				onclick={() => (selectedId = node.id)}
				ondragstart={(e) => {
					dragFromId = node.id;
					startX = e.clientX;
					dragIntent = null;
				}}
				ondragover={onDragOver}
				ondrop={onDrop}
			>
				<!-- Editable text -->
				<!-- <input
					type="text"
					value={node.text}
					oninput={(e) => {
						node.text = (e.target as HTMLInputElement).value;
						nodes = [...nodes]; // trigger reactivity
					}}
				/> -->
				<input type="text" bind:value={node.text} oninput={() => (nodes = [...nodes])} />
				<!-- Nested children -->
				{#if node.children?.length}
					<ListRenderer nodes={node.children} />
				{/if}
			</li>
		{/each}
	</ul>
</div>

<style>
	ul {
		list-style: none;
		padding-left: 1rem;
		margin: 0;
	}

	li {
		padding: 4px 6px;
		cursor: pointer;
		user-select: none;
	}

	.selected {
		outline: 2px solid dodgerblue;
	}

	input {
		border: none;
		background: transparent;
		width: 100%;
		font-size: 1em;
		padding: 2px 4px;
	}
</style>
