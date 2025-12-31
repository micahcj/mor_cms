<!-- <script lang="ts">
	type TreeNode = string | TreeNode[];

	const { nodes } = $props<{ nodes: TreeNode[] }>();
</script>

{#snippet render(nodes: TreeNode[])}
	<ul class="html-list">
		{#each nodes as node}
			{#if typeof node === 'string'}
				<li>{node}</li>
			{:else}
				<li>
					{node[0]}
					{#if node.length > 1}
						{@render render(node.slice(1))}
					{/if}
				</li>
			{/if}
		{/each}
	</ul>
{/snippet}

{@render render(nodes)} -->

<script lang="ts">
	import ListRenderer from './ListRenderer.svelte';
	import type { TreeNode } from '$lib/static_resources';
	import { findNode, indentNode, moveNodeById, outdentNode } from '$lib/utilities';

	interface Props {
		nodes: TreeNode[];
	}
	let { nodes }: Props = $props();

	let dragIntent: 'indent' | 'outdent' | null = $state(null);

	let selectedId = $state<string | null>(null);
	let dragFromId = $state<string | null>(null);
	let startX = 0;

	function handleKey(e: KeyboardEvent) {
		if (!selectedId) return;

		switch (true) {
			case e.key === 'Tab':
				e.preventDefault();
				nodes = e.shiftKey ? outdentNode(nodes, selectedId) : indentNode(nodes, selectedId);
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
		const found = findNode(nodes, selectedId!);
		if (!found) return;

		const container = found.parent ? found.parent.children! : nodes;
		const target = container[found.index + dir];
		if (!target) return;

		nodes = moveNodeById(nodes, selectedId!, target.id, dir === -1 ? 'before' : 'after');
	}

	function onDragOver(event: MouseEvent) {
		event.preventDefault();
		if (!dragFromId) return;
		const dx = event.clientX - startX;
		dragIntent = dx > 24 ? 'indent' : dx < -24 ? 'outdent' : null;
	}
</script>

<div tabindex="0" onkeydown={handleKey}>
	<ul>
		{#each nodes as node, i (i)}
			<li
				draggable
				tabindex="0"
				class:selected={selectedId === node.id}
				onclick={() => (selectedId = node.id)}
				ondragstart={(e) => {
					dragFromId = node.id;
					startX = e.clientX;
				}}
				ondragover={onDragOver}
				ondrop={() => {
					if (!dragFromId) return;

					if (dragIntent === 'indent') {
						nodes = indentNode(nodes, dragFromId);
					}
					if (dragIntent === 'outdent') {
						nodes = outdentNode(nodes, dragFromId);
					}

					dragFromId = dragIntent = null;
				}}
			>
				{node.text}

				{#if node.children}
					<ListRenderer nodes={node.children} />
				{/if}
			</li>
		{/each}
	</ul>
</div>

<style>
	li {
		padding: 4px 6px;
		cursor: pointer;
	}
	.selected {
		outline: 2px solid dodgerblue;
	}
</style>
