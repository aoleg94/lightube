<script>
	import { Tabs, TabList, TabPanel, Tab } from './tabs.js';
	import { need_update } from './stores.js';
	import { updateMetadata } from './mediasession.js';
	import ApiButton from './ApiButton.svelte';
	import TrackList from './TrackList.svelte';
	import PlayList from './PlayList.svelte';
	import Downloads from './Downloads.svelte';
	let state = {title: 'KEK', video: 'kek', position: 42, duration: 212, volume: 73, playing: false, mute: false,
		playlist: [], audio_tracks: [], sub_tracks: []};
	let newurl = "https://www.youtube.com/watch?v=LXb3EKWsInQ";
	let n = 0;
	let need_update_var = true;
	need_update.subscribe(v => {
		if(!v) return;
		fetch('/api/status2').then(resp => resp.json()).then(js => {
			state = js;
			need_update.set(false);
			updateMetadata(state);
		});
	});
	setInterval(() => {
		fetch('/api/status').then(resp => resp.json()).then(js => {
			if(js.playlist_pos != state.playlist_pos)
				need_update.set(true);
			for(var key in js)
				state[key] = js[key];
			updateMetadata(state);
		});
		n = n > 10 ? 0 : n + 1;
		if(n === 0)
			need_update.set(true);
	}, 250);
	need_update.set(true);

	function seek(e) {
		var v = e.target.value;
		fetch('/api/seek/abs/' + v, {method: 'POST'});
	};
	function vol(e) {
		var v = e.target.value;
		fetch('/api/vol/abs/' + v, {method: 'POST'});
	};
	function hms(s) {
		if(s === null || s === undefined)
			return '--:--';
		var h = Math.floor(s / 3600);
		s = s % 3600;
		var m = Math.floor(s / 60);
		s = Math.floor(s % 60);
		return h.toString() + ':' +
			m.toString().padStart(2, '0') + ':' +
			s.toString().padStart(2, '0');
	};

	const MAX_QUALITY = 999999999;
	const QUALITY_VARIANTS = [MAX_QUALITY, 2160, 1080, 720, 480, 360, 240, 144];
</script>

<style>
	h1 {
		text-align: center;
	}
	.w100 {
		width: 98%;
	}
	.w40 {
		width: 40%;
	}
	.selected {
		font-weight: bold;
	}
</style>

<span>{state.title || "No video"}</span>
<br/>
<a href={state.video}>{state.video || ""}</a>
<br/>
New URL:<input class=w100 type=text bind:value={newurl} maxlen/>
<br/>
<ApiButton text="Play Now" uri={"/api/load/"+encodeURIComponent(newurl)}/>
<ApiButton text=Prepend uri={"/api/add/"+encodeURIComponent(newurl)}/>
<ApiButton text=Close uri={"/api/reinit"}/>
<br/>
<br/>
Seek: {hms(state.position)} / {hms(state.duration)}
<input class=w100 type=range min=0 value={state.position} max={state.duration} on:change={seek}/>
<br/>
<br/>
<ApiButton text="⏮" uri="/api/seek/rel/-60"/>
<ApiButton text="⏪" uri="/api/seek/rel/-5"/>
{#if !state.playing}
<ApiButton text="▶️" uri="/api/play"/>
{:else}
<ApiButton text="⏸" uri="/api/pause"/>
{/if}
<ApiButton text="⏩" uri="/api/seek/rel/5"/>
<ApiButton text="⏭" uri="/api/seek/rel/60"/>
<br/>
<br/>
<br/>
Volume: {state.volume}%
<input class=w100 type=range min=0 value={state.volume} max=130 on:change={vol}/>
<br/>
<br/>
<ApiButton text={state.mute ? "🔈" : "🔇"} uri="/api/mute"/>
<ApiButton text="🔉" uri="/api/vol/rel/-5"/>
<ApiButton text="🔊" uri="/api/vol/rel/5"/>
<br/>
<ApiButton text="👂" uri="/api/cycle/audio"/>
<ApiButton text="🔡" uri="/api/cycle/sub"/>
<ApiButton text="🎚" uri="/api/cyclev/af/loudnorm=I=-30 loudnorm=I=-15 anull"/>
<br/>
<!--ApiButton text="⏮" uri="/api/prev"/-->
<ApiButton text="⏪" uri="/api/speed/down"/>
<ApiButton text="🕛" uri="/api/speed/abs/1"/>
<ApiButton text="⏩" uri="/api/speed/up"/>
<!--ApiButton text="⏭" uri="/api/next"/-->
<br/>
<br/>
<Tabs>
	<TabList>
		<Tab>Playlist</Tab>
		<Tab>Audio Tracks</Tab>
		<Tab>Subtitles</Tab>
		<Tab>File system</Tab>
		<Tab>Quality</Tab>
	</TabList>

	<TabPanel>
		<PlayList playlist={state.playlist} />
	</TabPanel>

	<TabPanel>
		<TrackList tracks={state.audio_tracks} kind='audio'/>
	</TabPanel>

	<TabPanel>
		<TrackList tracks={state.sub_tracks} kind='sub'/>
	</TabPanel>

	<TabPanel>
		<table>
		{#each state.movies as m}
			<tr><td><ApiButton small={true} text="+" uri={"/api/load/file://"+encodeURIComponent(m.full)}/><span>&nbsp;{m.name}</span></td></tr>
		{/each}
		</table>
		<ApiButton text="Scan movies" uri="/api/scan"/>
	</TabPanel>

	<TabPanel>
		<br/>
		Current max quality: {state.quality == MAX_QUALITY ? "Max" : state.quality+"p"}
		<ul>
		{#each QUALITY_VARIANTS as q}
		<li><a class:selected={state.quality == q} on:click={e => fetch("/api/maxres/"+q, {method: 'POST'})} >{q == MAX_QUALITY ? "Max" : q+"p"}</a></li>
		{/each}
		</ul>
	</TabPanel>

	<TabPanel>
		<Downloads state={state.downloads || {}} />
	</TabPanel>
</Tabs>
