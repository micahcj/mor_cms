<script lang="ts">
	import type { TreeNode } from '$lib/static_resources2';
	import { onMount } from 'svelte';

	interface Props {
		nodes: TreeNode[];
		onIndent: (id: string) => void;
		onOutdent: (id: string) => void;
		onEdit: (id: string, value: string) => void;
		onReorder: (fromId: string, toId: string, position: 'before' | 'after') => void;
		// Props for coordinating drag state across recursive instances
		sharedDragState?: { dragFromId: string | null; startX: number };
		depth?: number;
	}

	let {
		nodes,
		onIndent,
		onOutdent,
		onEdit,
		onReorder,
		sharedDragState = $bindable({ dragFromId: null, startX: 0 }),
		depth = 0
	}: Props = $props();

	let selectedId = $state<string | null>(null);
	let dropTargetId = $state<string | null>(null);
	let dropPosition = $state<'before' | 'after' | null>(null);
	let dragDirection = $state<'horizontal' | 'vertical' | null>(null);
	let indentDirection = $state<'indent' | 'outdent' | null>(null);

	function handleKey(e: KeyboardEvent) {
		if (!selectedId) return;
		if (e.key === 'Tab') {
			e.preventDefault();
			if (e.shiftKey) {
				onOutdent(selectedId);
			} else {
				onIndent(selectedId);
			}
		}
	}

	function handleDragStart(e: DragEvent, id: string) {
		e.stopPropagation();
		console.log('drag start:', id);

		sharedDragState.dragFromId = id;
		sharedDragState.startX = e.clientX;

		// Set drag image to make it clearer
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
		}
	}

	function handleDragOver(e: DragEvent, id: string) {
		e.preventDefault();
		e.stopPropagation();

		if (!sharedDragState.dragFromId) return;

		// Calculate drag distance from start position
		const dx = e.clientX - sharedDragState.startX;

		// Determine if horizontal or vertical drag based on distance
		if (Math.abs(dx) > 24) {
			// Horizontal drag - indent/outdent
			dragDirection = 'horizontal';
			indentDirection = dx > 24 ? 'indent' : 'outdent';
			dropTargetId = null;
			dropPosition = null;
		} else if (sharedDragState.dragFromId !== id) {
			// Vertical drag - reorder (only if not over self)
			dragDirection = 'vertical';
			indentDirection = null;

			// Determine if we're in top or bottom half of element
			const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
			const midpoint = rect.top + rect.height / 2;

			dropTargetId = id;
			dropPosition = e.clientY < midpoint ? 'before' : 'after';
		}
	}

	function handleDragLeave(e: DragEvent) {
		e.stopPropagation();
		// Only clear if we're leaving the actual target, not a child
		if (e.currentTarget === e.target) {
			dropTargetId = null;
			dropPosition = null;
		}
	}

	function handleDrop(e: DragEvent, id: string) {
		e.preventDefault();
		e.stopPropagation();

		console.log('drop on:', id, 'position:', dropPosition);

		if (!sharedDragState.dragFromId || sharedDragState.dragFromId === id) {
			cleanup();
			return;
		}

		// Check for indent/outdent based on horizontal drag
		const dx = e.clientX - sharedDragState.startX;

		if (Math.abs(dx) > 24) {
			// Horizontal drag - indent or outdent
			if (dx > 24) {
				onIndent(sharedDragState.dragFromId);
			} else if (dx < -24) {
				onOutdent(sharedDragState.dragFromId);
			}
		} else {
			// Vertical drag - reorder
			console.log('Reordering', sharedDragState.dragFromId, dropPosition, id);
			onReorder(sharedDragState.dragFromId, id, dropPosition!);
		}

		cleanup();
	}

	function handleDragEnd() {
		cleanup();
	}

	function cleanup() {
		sharedDragState.dragFromId = null;
		sharedDragState.startX = 0;
		dropTargetId = null;
		dropPosition = null;
		dragDirection = null;
		indentDirection = null;
	}

	function getDropIndicatorClass(nodeId: string): string {
		if (dropTargetId !== nodeId) return '';
		return dropPosition === 'before' ? 'drop-before' : 'drop-after';
	}

	function getIndentClass(nodeId: string): string {
		if (sharedDragState.dragFromId === nodeId && indentDirection) {
			// Calculate target depth during drag
			const targetDepth = indentDirection === 'indent' ? depth + 1 : Math.max(0, depth - 1);
			return `depth-${targetDepth}`;
		}
		return `depth-${depth}`;
	}

	onMount(() => {
		console.log('textobjs', $state.snapshot(nodes));
	});
</script>

<ul>
	{#each nodes as node (node.id)}
		<li
			draggable="true"
			tabindex="0"
			class:selected={selectedId === node.id}
			class:dragging={sharedDragState.dragFromId === node.id}
			class:will-indent={sharedDragState.dragFromId === node.id && indentDirection === 'indent'}
			class:will-outdent={sharedDragState.dragFromId === node.id && indentDirection === 'outdent'}
			class={`${getDropIndicatorClass(node.id)} ${getIndentClass(node.id)}`}
			onclick={() => (selectedId = node.id)}
			ondragstart={(e) => handleDragStart(e, node.id)}
			ondragover={(e) => handleDragOver(e, node.id)}
			ondragleave={handleDragLeave}
			ondrop={(e) => handleDrop(e, node.id)}
			ondragend={handleDragEnd}
			onkeydown={handleKey}
			onfocus={() => (selectedId = node.id)}
		>
			<span class="node-content">{node.text}</span>

			{#if node.children?.length}
				<svelte:self
					nodes={node.children}
					{onIndent}
					{onOutdent}
					{onEdit}
					{onReorder}
					bind:sharedDragState
					depth={depth + 1}
				/>
			{/if}
		</li>
	{/each}
</ul>

<style>
	ul {
		list-style: none;
		padding-left: 0;
		margin: 0.25rem 0;
	}

	li {
		padding: 0.5rem;
		margin: 0.25rem 0;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		cursor: move;
		position: relative;
		background: white;
		transition:
			left 0.2s ease,
			background-color 0.2s;
	}

	/* Indent levels */
	li.depth-0 {
		left: 0;
	}

	li.depth-1 {
		left: 2rem;
	}

	li.depth-2 {
		left: 4rem;
	}

	li.depth-3 {
		left: 6rem;
	}

	li.depth-4 {
		left: 8rem;
	}

	li:hover {
		background-color: #f5f5f5;
	}

	.selected {
		outline: 2px solid dodgerblue;
	}

	.dragging {
		opacity: 0.5;
		cursor: grabbing;
	}

	.will-indent {
		border-left: 3px solid #4caf50;
	}

	.will-outdent {
		border-left: 3px solid #ff9800;
	}

	.drop-before::before {
		content: '';
		position: absolute;
		top: -2px;
		left: 0;
		right: 0;
		height: 3px;
		background-color: dodgerblue;
	}

	.drop-after::after {
		content: '';
		position: absolute;
		bottom: -2px;
		left: 0;
		right: 0;
		height: 3px;
		background-color: dodgerblue;
	}

	.node-content {
		user-select: none;
		display: inline-block;
	}
</style>
