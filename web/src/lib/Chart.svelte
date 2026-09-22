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
		const ro = new ResizeObserver(() => { if (sized()) chart?.resize(); });
		ro.observe(el);
		return () => {
			ro.disconnect();
			chart?.dispose();
		};
	});

	// notMerge stays true: the map series genuinely swaps between pt-distritos
	// and portugal, and merging would keep the old geometry registered.
	$effect(() => {
		if (chart && option && sized()) chart.setOption(option as never, true);
	});
</script>

<div bind:this={el} style:height role="img" aria-label={ariaLabel || t('chart.default')}></div>
