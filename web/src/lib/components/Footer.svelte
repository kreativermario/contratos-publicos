<script lang="ts">
	import { L, t } from '$lib/messages';

	// `caveats` are keys, not sentences: the API stopped shipping prose when the
	// site went bilingual. An unknown key renders as itself, which is visible.
	let { caveats = [], latest = null }: { caveats?: string[]; latest?: string | null } = $props();
</script>

<footer>
	<div class="stripe" aria-hidden="true"></div>
	<div class="wrap inner">
		<div>
			<h3>{t('common.site')}</h3>
			<p class="blurb">{t('footer.blurb')}</p>
		</div>

		<div>
			<p class="eyebrow">{t('footer.sourceHead')}</p>
			<ul>
				<li><a href="https://dados.gov.pt" rel="noreferrer noopener external">IMPIC / dados.gov.pt</a>, {t('footer.rawData')}</li>
				<li><a href="https://www.base.gov.pt" rel="noreferrer noopener external">Base.gov.pt</a>, {t('footer.officialPortal')}</li>
				<li><a href="/api/docs">{t('footer.api')}</a>, {t('footer.apiNote')}</li>
				<li><a href={L('/termos')}>{t('footer.terms')}</a>, {t('footer.termsNote')}</li>
				<!-- AGPL section 13: anyone interacting with this over a network must be
				     offered the source. This link is that offer, so it is not decoration
				     and must not be removed. -->
				<li><a href="https://github.com/kreativermario/contratos-publicos" rel="noreferrer noopener external">{t('footer.code')}</a>, {t('footer.codeNote')}</li>
				{#if latest}<li>{t('footer.latest')}: <span class="num">{latest}</span></li>{/if}
			</ul>
		</div>

		<div class="small">
			<p class="eyebrow">{t('footer.disclaimerHead')}</p>
			<ul>
				{#each caveats as c}<li>{t(`disclaimer.${c}`)}</li>{/each}
				<li><strong>{t('footer.noCrimeStrong')}</strong> {t('footer.noCrimeBody')}
				<a href={L('/termos')}>{t('footer.termsFull')}</a>.</li>
				<!-- Only the English build has anything to say here: the register's own
				     text is Portuguese and stays Portuguese. Empty in pt, so nothing
				     renders. -->
				{#if t('common.verbatim')}<li>{t('common.verbatim')}</li>{/if}
			</ul>
		</div>
	</div>
</footer>

<style>
	footer { margin-top: 4rem; background: var(--ink); color: #f3e2c8; position: relative; z-index: 1; }
	.stripe { height: 5px; background: linear-gradient(90deg,
		var(--manjerico) 0 25%, var(--azulejo) 25% 50%, var(--amarelo) 50% 75%, var(--sangria) 75% 100%); }
	.inner { display: grid; grid-template-columns: 1.2fr 1fr 1.4fr; gap: 2.5rem; padding: 2.5rem 0 3rem; }
	h3 { color: var(--amarelo); font-size: 1.5rem; }
	.blurb { color: #c9b39a; max-width: 26ch; }
	ul { list-style: none; margin: .4rem 0 0; padding: 0; display: grid; gap: .45rem; font-size: .85rem; color: #c9b39a; }
	.small li { line-height: 1.45; }
	a { color: var(--amarelo); }
	:global(footer .eyebrow) { color: #9c8078; }
	@media (max-width: 860px) { .inner { grid-template-columns: 1fr; gap: 1.75rem; } }
</style>
