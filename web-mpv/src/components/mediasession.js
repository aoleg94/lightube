import { need_update } from './stores.js';

function act(uri) {
	fetch(uri, {method: 'POST'});
	need_update.set(true);
}

var audioTag = null;
export function setupNotification(pause) {
	if (!audioTag && 'mediaSession' in navigator) {
		audioTag = document.createElement('audio');
		document.body.appendChild(audioTag);
		audioTag.src = "/static/10-seconds-of-silence.mp3";
		audioTag.loop = true;
		audioTag.play();
	}
	if(pause)
		audioTag.pause();
	else
		audioTag.play();
}

export function updateMetadata(state) {
	if('mediaSession' in navigator) {
		navigator.mediaSession.metadata = state.title ? new MediaMetadata({title: state.title}) : null;
		navigator.mediaSession.playbackState = !state.duration ? 'none' : (state.playing ? 'playing' : 'paused')
		/* Position state (supported since Chrome 81) */
		if ('setPositionState' in navigator.mediaSession) {
			navigator.mediaSession.setPositionState(!state.duration ? null : {
				duration: state.duration,
				playbackRate: state.speed,
				position: state.position
			});
		}
	}
}

/* Previous Track & Next Track */

if('mediaSession' in navigator) {
	navigator.mediaSession.setActionHandler('previoustrack', function() {
		act('/api/prev');
	});

	navigator.mediaSession.setActionHandler('nexttrack', function() {
		act('/api/next');
	});

	/* Seek Backward & Seek Forward */

	let defaultSkipTime = 10; /* Time to skip in seconds by default */
	navigator.mediaSession.setActionHandler('seekbackward', function(event) {
		act('/api/seek/rel/-10');
	});

	navigator.mediaSession.setActionHandler('seekforward', function(event) {
		act('/api/seek/rel/10');
	});

	/* Play & Pause */

	navigator.mediaSession.setActionHandler('play', function() {
		act('/api/play');
	});

	navigator.mediaSession.setActionHandler('pause', function() {
		act('/api/pause');
	});

	/* Stop (supported since Chrome 77) */

	/*try {
		navigator.mediaSession.setActionHandler('stop', function() {
			//act('/api/pause');
		});
	} catch(error) {
	}*/

	/* Seek To (supported since Chrome 78) */

	try {
		navigator.mediaSession.setActionHandler('seekto', function(event) {
			act('/api/seek/abs/'+(event.seekTime|0));
		});
	} catch(error) {
	}
}
