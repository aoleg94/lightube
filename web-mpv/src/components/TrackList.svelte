<script>
	export let tracks;
	export let kind;

	/*import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	function setTrack(id) {
		dispatch('settrack', {
			id: id
		});
	}*/
	import { need_update } from './stores.js';

	function setTrack(id) {
		fetch('/api/setprop/' + kind + '/' + id, {method: 'POST'});
		need_update.set(true);
	}

	function anySelected(tt) {
		for(var x of tt) {
			if(x.selected)
				return true;
		}
		return false;
	}
</script>

<style>
	.selected {
		font-weight: bold;
	}
</style>

<ol>
	<li><a class:selected={!anySelected(tracks)} on:click={e => setTrack(false)} >Off</a></li>
	{#each tracks as t}
		<li><a class:selected={t.selected} on:click={e => setTrack(t.id)} >{t.lang}</a></li>
	{/each}
</ol>
