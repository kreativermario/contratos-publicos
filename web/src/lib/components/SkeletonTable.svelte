<script lang="ts">
	// Stands in for a whole table, header row included, so nothing shifts when
	// the real rows arrive. Column widths mirror the table it replaces.
	let { rows = 6, cols = ['38%', '22%', '14%', '12%'], twoLine = true }: {
		rows?: number; cols?: string[];
		/** the first column carries an object plus its date, so it is two lines tall */
		twoLine?: boolean;
	} = $props();
</script>

<div class="sk-table" aria-hidden="true">
	<div class="sk-head">
		{#each cols as w}<span class="sk" style:width="min({w}, 7rem)"></span>{/each}
	</div>
	{#each Array.from({ length: rows }) as _, r}
		<div class="sk-row">
			{#each cols as w, i}
				{#if i === 0 && twoLine}
					<span class="first" style:width={w}>
						<span class="sk"></span>
						<span class="sk date"></span>
					</span>
				{:else}
					<span class="sk" style:width={w}></span>
				{/if}
			{/each}
		</div>
	{/each}
</div>

<style>
	.sk-table { padding: 0 .9rem; }
	.sk-head, .sk-row { display: flex; align-items: center; gap: 1rem; }
	.sk-head { height: 2.55rem; border-bottom: 2px solid var(--ink); }
	.sk-head .sk { height: .55rem; flex: none; }
	.sk-row { height: 5.6rem; border-bottom: 1px solid var(--rule); }
	.sk-row:last-child { border-bottom: 0; }
	.sk-row .sk { height: .85rem; flex: none; }
	.first { display: flex; flex-direction: column; gap: .35rem; flex: none; }
	.first .sk { width: 100%; }
	.first .date { width: 45%; height: .6rem; }

	/* below the break the real table stacks into per-row cards, which are taller
	   and single column; the skeleton has to stack with it or it undershoots */
	@media (max-width: 820px) {
		.sk-head { display: none; }
		.sk-row { height: auto; flex-direction: column; align-items: stretch; gap: .45rem; padding: .7rem 0; }
		.sk-row .sk, .first { width: 100% !important; }
	}
</style>
