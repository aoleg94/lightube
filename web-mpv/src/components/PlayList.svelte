<script>
	import ApiButton from './ApiButton.svelte';
	export let playlist;

	/*import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	function setTrack(id) {
		dispatch('settrack', {
			id: id
		});
	}*/
	import { need_update } from './stores.js';

	function setTrack(id) {
		fetch('/api/setprop/playlist_pos/' + id, {method: 'POST'});
		need_update.set(true);
	}

	function getIcon(t) {
		return t.current ? "▶" : "⏯";
	}
</script>

<style>
	.selected {
		font-weight: bold;
	}
	.max {
		width: 100%;
	}
</style>

<table class=max>
	{#each playlist as t,id}
		<tr>
			<td class=max>
				{#if t.current}
					<ApiButton small={true} text="⏯" uri="/api/play"/>
				{:else}
					<ApiButton small={true} text="▶" uri="/api/setprop/playlist_pos/{id}"/>
				{/if}
				<a href="{t.filename}" class:selected={t.current} >{t.title || t.filename}</a>
			</td>
			<td><ApiButton small={true} text="⏫" uri="/api/move/{id}/{id-1}"/></td>
			<td><ApiButton small={true} text="⏬" uri="/api/move/{id}/{id+2}"/></td>
			<td><ApiButton small={true} text="❌" uri="/api/remove/{id}"/></td>
		</tr>
	{/each}
</table>
{#if playlist.length > 0}
<ApiButton text="Clear" uri="/api/clear"/>
{/if}
<!-- ⏫ up ⏬ down -->
