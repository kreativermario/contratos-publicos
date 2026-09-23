<script lang="ts">
	import echarts from '$lib/echarts';
	import { t } from '$lib/messages';
	import { onMount } from 'svelte';

	// This ~25-line wrapper is the entire cost of Svelte not having vue-echarts.
	let { option, height = '420px', ariaLabel = '', onpick }: {
		option: unknown; height?: string; ariaLabel?: string;
		/** fires with the clicked datum, so a chart can drive a detail panel */
		onpick?: (data: any) => void;
	} = $props();

	let el: HTMLDivElement;
	const sized = () => Boolean(el?.clientWidth && el?.clientHeight);
	let chart = $state<ReturnType<typeof echarts.init> | undefined>();
	/** whether the current option has actually been handed to ECharts */
	let drawn = false;

	function draw() {
		if (!chart || !option || !sized()) return;
		// notMerge stays true: the map series genuinely swaps between pt-distritos
		// and portugal, and merging would keep the old geometry registered.
		chart.setOption(option as never, true);
		drawn = true;
	}

	onMount(() => {
		chart = echarts.init(el, undefined, { renderer: 'canvas' });
		chart.on('click', (p: any) => {
			if (p.dataType === 'edge') return;
			onpick?.(p.data);
		});
		// zrender inverts the geo transform on every resize, and invert() returns
		// null for a singular matrix, which the caller then dereferences. The
		// matrix goes singular whenever the box has collapsed in one axis, which
		// is exactly what a hidden tab panel or a mid-transition card looks like.
		// resize, but also draw. The effect below refuses to setOption on a box
		// with no size, and nothing used to retry: a panel that was unsized at
		// the moment the option arrived kept an empty chart for good, which is
		// what "the graph never loads" looked like. The observer is the one
		// thing that knows when the box gained a size, so it is what retries.
		const ro = new ResizeObserver(() => {
			if (!sized()) return;
			if (drawn) chart?.resize();
			else draw();
		});
		ro.observe(el);
		return () => {
			ro.disconnect();
			chart?.dispose();
		};
	});

	$effect(() => {
		option;        // re-run when a new option arrives, drawn or not
		drawn = false;
		draw();
	});
</script>

<div bind:this={el} style:height role="img" aria-label={ariaLabel || t('chart.default')}></div>
