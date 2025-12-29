<script lang="ts">
	import TextButton from '$lib/Components/TextButton.svelte';
	import { indentValues, type IndentValue, type TextObject } from '$lib/static_resources';

	const defaultTextObj: TextObject = { text: 'default', indentValue: 'Main' };
	let textObjs: TextObject[] = $state([
		{ text: 'shid1', indentValue: 'Main' },
		{ text: 'shid2', indentValue: 'Main' }
	]);

	function addTextObj(index: number) {
		const insertIndex = index + 1;
		textObjs = [...textObjs.slice(0, insertIndex), defaultTextObj, ...textObjs.slice(index, -1)];
	}
	function removeTextObj(index: number) {
		if (textObjs.length < 2) {
			// alert('FUTURE');
			return;
		}
		textObjs.splice(index);
	}

	//^^ turn that into a store.
	/*TODO
forEach textele push to array after completion
or reform array after each modification. 
queryselectorall?
onchange?
*/
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>

<div class="content" onchange={() => console.log($state.snapshot(textObjs))}>
	{#each textObjs as obj, i (i)}
		<div class="textbutton-container">
			<div class="plus-minus">
				<button onclick={() => addTextObj(i)}>+</button>
				<button onclick={() => removeTextObj(i)}>-</button>
			</div>
			<TextButton text={obj.text} indentValue={obj.indentValue}></TextButton>
		</div>
	{/each}
</div>

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
</style>
