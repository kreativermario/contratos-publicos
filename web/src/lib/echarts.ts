// Tree-shaken ECharts: the barrel import pulls ~1MB, this pulls what we draw.
import * as echarts from 'echarts/core';
import { BarChart, GraphChart, MapChart } from 'echarts/charts';
import {
	GridComponent, LegendComponent, TooltipComponent, VisualMapComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
	BarChart, GraphChart, MapChart,
	GridComponent, LegendComponent, TooltipComponent, VisualMapComponent,
	CanvasRenderer
]);

export default echarts;
export type { EChartsOption } from 'echarts';

export const INK = '#240706';
export const INK_SOFT = '#6b4a44';
export const PAPER_2 = '#fffcef';
export const RULE = '#e2c3a8';

/** Shared tooltip chrome: stamped card, not a floating grey box. */
export const tooltipBase = {
	// on a 360px screen an unconfined tooltip renders at a negative left and
	// half the supplier name falls off the edge
	confine: true,
	backgroundColor: PAPER_2,
	borderColor: INK,
	borderWidth: 2,
	padding: [10, 12],
	textStyle: { color: INK, fontSize: 13, fontFamily: 'Archivo, sans-serif' },
	// ECharts writes white-space:nowrap on the tooltip element, so max-width alone
	// does nothing: the box just grows past the chart. Portuguese firm names run
	// long ("Uniself - Sociedade de Restaurantes Públicos e Privados, S.A."), so
	// say normal explicitly, and let a single unbroken token break rather than
	// push the box wide.
	extraCssText: 'box-shadow: 4px 4px 0 #240706; border-radius: 4px; max-width: 320px;'
		+ ' white-space: normal; overflow-wrap: anywhere;'
};

export const FONT = 'Archivo, Helvetica Neue, Arial, sans-serif';
export const DISPLAY = 'Bowlby One, Archivo Black, Impact, sans-serif';
