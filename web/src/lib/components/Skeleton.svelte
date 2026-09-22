<script lang="ts">
	// One placeholder bar, or a stack of them, shaped like the content it stands
	// in for. The shimmer itself lives in app.css so every skeleton sweeps alike.
	let { w = '100%', h = '1rem', lines = 1, gap = '.5rem', last = '62%' }: {
		w?: string; h?: string; lines?: number; gap?: string;
		/** width of the final line, so a paragraph does not end square */
		last?: string;
	} = $props();
</script>

{#if lines > 1}
	<span class="stack" aria-hidden="true" style:gap>
		{#each Array.from({ length: lines }) as _, i}
			<span class="sk" style:width={i === lines - 1 ? last : w} style:height={h}></span>
		{/each}
	</span>
{:else}
	<span class="sk" aria-hidden="true" style:width={w} style:height={h}></span>
{/if}

<style>
	.stack { display: flex; flex-direction: column; }
</style>
