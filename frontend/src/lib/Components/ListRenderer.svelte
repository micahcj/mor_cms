<script lang="ts">
	type Node = string | Node[];

	const { nodes } = $props<{ nodes: Node[] }>();
</script>

{#snippet render(nodes: Node[])}
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

{@render render(nodes)}
