<script>
	export let uri;
	export let text;
	export let small = false;
	export let pause = false;

	import { need_update } from './stores.js';
	import { setupNotification } from './mediasession.js';

	function act() {
		fetch(uri, {method: 'POST'});
		need_update.set(true);
		setupNotification(pause);
	}
</script>

<style>
button {
  padding: 0;
  border: none;
  font: inherit;
  color: inherit;
  background-color: transparent;
}
.btn {
  /* default for <button>, but useful for <a> */
  display: inline-block;
  text-align: center;
  text-decoration: none;

  /* create a small space when buttons wrap on 2 lines */
  margin: 2px 0;

  /* invisible border (will be colored on hover/focus) */
  border: solid 1px transparent;
  border-radius: 4px;

  /* size comes from text & padding (no width/height) */
  padding: 1em 1em;

  /* make sure colors have enough contrast! */
  color: #ffffff;
  background-color: #3366cc; /*#9555af;*/
}
/* old-school "down" effect on click + color tweak */
.btn:active {
  transform: translateY(1px);
  filter: saturate(150%);
}
/* inverse colors on mouse-over */
.btn:hover {
  color: #3366cc; /*#9555af;*/
  border-color: currentColor;
  background-color: white;
}
.small {
	padding: 0.6em 0.6em;
}
</style>

<a class=btn class:small on:click={act}>{text}</a>
