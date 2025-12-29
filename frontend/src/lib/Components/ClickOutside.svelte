<script lang="ts">
	import { browser } from '$app/environment';
	import { onDestroy, onMount, type Snippet } from 'svelte';
	interface Props {
		children: Snippet;
		onClickOutside: VoidFunction;
	}

	let container: HTMLElement;
	let { children, onClickOutside }: Props = $props();
	const eventList = ['mousedown', 'dragstart', 'touchstart'];
	function containerContains(element: HTMLElement) {
		return container === element || container.contains(element);
	}

	function clickHandler(event: Event) {
		const e = event as MouseEvent;

		if (containerContains(document.activeElement as HTMLElement)) {
			if (!containerContains((e.target as HTMLElement) ?? e.currentTarget)) {
				// if ((e.target as HTMLElement).closest('select, option, button, input, label')) {
				// 	return;
				// }
				onClickOutside();
			}
		}
	}

	onMount(() => {
		if (!browser) return;
		eventList.forEach((eventName) => document.addEventListener(eventName, clickHandler));
	});

	onDestroy(() => {
		if (!browser) return;
		eventList.forEach((eventName) => document.removeEventListener(eventName, clickHandler));
	});
</script>

<div class="outside" bind:this={container} tabindex="-1">
	{@render children()}
</div>

<style>
	.outside {
		position: absolute;
		width: 100%;
		height: auto;
	}
</style>
