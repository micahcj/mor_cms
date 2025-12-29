<script lang="ts">
	import { onMount, tick } from 'svelte';
	import ClickOutside from './ClickOutside.svelte';
	import { indentValues, type IndentValue } from '$lib/static_resources';

	let {
		text = $bindable('shid'),
		indentValue = $bindable(indentValues[0])
	}: { text: string; indentValue: IndentValue } = $props();

	// let text = $state('Shiiiiid');
	let buttonEle: HTMLButtonElement;
	let textMode: boolean = $state(false);
	let inputEle: HTMLTextAreaElement;
	// let indentValue: IndentValue = $state(indentValues[0]);

	async function textOn() {
		textMode = true;
		// await tick();
		if (inputEle) {
			console.log(inputEle);
			await tick();
			inputEle.focus();
		}
	}

	function textOff() {
		textMode = false;
	}
	// onMount( ()=>{
	//     buttonEle.addEventListener('focus')
	// })
</script>

<div class="text-container">
	<select bind:value={indentValue}>
		{#each indentValues as indent (indentValues.indexOf(indent))}
			<option>{indent}</option>
		{/each}
	</select>
	<div>
		<ClickOutside onClickOutside={textOff}>
			<button
				bind:this={buttonEle}
				onclick={textOn}
				class="button-container {indentValue.valueOf().toLocaleLowerCase()}"
				>{#if !textMode}
					{text}
				{/if}

				<textarea
					bind:this={inputEle}
					bind:value={text}
					class="input-button {textMode ? 'show' : 'hide'}"
				></textarea>
			</button>
		</ClickOutside>
	</div>
</div>

<style>
	.text-container {
		display: flex;
		gap: 1rem;
	}
	.button-container {
		display: flex;
		background: none;
		border: none;
	}

	.input-button {
		min-width: 5rem;
		min-height: 3rem;
	}

	.show {
		display: flex;
	}

	.hide {
		display: none;
	}

	.main {
		font-weight: 500;
		font-size: medium;
	}

	.bullet {
		position: relative;
		left: 1rem;
		font-size: small;
	}
	.sub-bullet {
		position: relative;
		left: 2rem;
		font-size: smaller;
	}
</style>
