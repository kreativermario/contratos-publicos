<script lang="ts">
	import type { Company } from '$lib/api';
	import Skeleton from '$lib/components/Skeleton.svelte';
	import { t } from '$lib/messages';

	let { company, busy = false, name = '' }: {
		company: Company | null;
		busy?: boolean;
		/** the name the contract record uses, so the registry name is only shown
		 *  when it actually differs */
		name?: string;
	} = $props();

	const differs = $derived(
		Boolean(company?.sicae_name) &&
		company!.sicae_name!.toLocaleLowerCase('pt-PT') !== name.toLocaleLowerCase('pt-PT')
	);
</script>

{#if busy}
	<div class="profile" aria-busy="true">
		<div class="sk-dl">
			{#each Array.from({ length: 3 }) as _, i (i)}
				<Skeleton w="5.5rem" h=".7rem" />
				<Skeleton w="72%" h=".9rem" />
			{/each}
		</div>
		<Skeleton w="11rem" h=".65rem" />
		<div class="sk-caes">
			{#each ['86%', '73%', '79%', '64%', '81%', '69%', '58%'] as w (w)}
				<Skeleton {w} h=".84rem" />
			{/each}
		</div>
		<Skeleton lines={3} h=".7rem" gap=".38rem" last="46%" />
	</div>
{:else if !company}
	<p class="profile miss">{t('reg.missing')}</p>
{:else}
	<div class="profile">
		<dl>
			{#if differs}<dt>{t('reg.registeredName')}</dt><dd>{company.sicae_name}</dd>{/if}
			{#if company.legal_form}<dt>{t('reg.form')}</dt><dd>{company.legal_form}</dd>
			{:else if company.legal_type}<dt>{t('reg.type')}</dt><dd>{company.legal_type}</dd>{/if}
			{#if company.founded_year}
				<dt>{t('reg.founded')}</dt>
				<dd>
					{#if company.founded_exact}
						{t('reg.foundedIn')} <span class="num">{company.founded_year}</span>
					{:else}
						<span class="num">{company.founded_year}</span> {t('reg.foundedOrEarlier')}
					{/if}
				</dd>
			{/if}
			{#if company.address}<dt>{t('reg.address')}</dt><dd class="addr">{company.address}</dd>{/if}
		</dl>

		{#if company.cae.length}
			<p class="eyebrow">{t('reg.activities')}</p>
			<ul class="caes">
				{#each company.cae as k (k.code)}
					<li class:principal={k.type === 'principal'}>
						<b class="num">{k.code}</b>
						<span>{k.description ?? t('common.na')}</span>
						{#if k.type === 'principal'}<i>{t('reg.principal')}</i>{/if}
					</li>
				{/each}
			</ul>
		{/if}

		<p class="src">
			{t('reg.sourceLine', { source: company.source === 'sicae' ? 'SICAE' : 'SICAE + VIES' })}
			{#if company.founded_year && !company.founded_exact}
				{t('reg.floorNote', { year: company.founded_year })}{/if}
			{t('reg.noCapital')}
		</p>
	</div>
{/if}

<style>
	.profile { padding: .2rem 1rem 1rem; border-bottom: 1px solid var(--rule); }
	.profile.miss { margin: 0; padding: .2rem 1rem 1rem; font-size: .85rem; color: var(--ink-soft);
		max-width: 62ch; line-height: 1.45; }
	.profile dl { display: grid; grid-template-columns: max-content minmax(0, 1fr);
		gap: .3rem .9rem; margin: 0 0 1rem; font-size: .86rem; align-items: baseline; }
	.profile dt { font-size: .66rem; font-weight: 700; text-transform: uppercase;
		letter-spacing: .09em; color: var(--ink-faint); white-space: nowrap; }
	.profile dd { margin: 0; }
	.profile .addr { white-space: pre-line; line-height: 1.35; }

	.caes { list-style: none; margin: .4rem 0 1rem; padding: 0; display: grid; gap: .35rem; }
	.caes li { display: flex; align-items: baseline; flex-wrap: wrap; gap: .3rem .6rem;
		font-size: .84rem; color: var(--ink-soft); }
	.caes li b { font-weight: 700; color: var(--ink-soft); font-size: .82rem; flex: none; }
	.caes li.principal { color: var(--ink); }
	.caes li.principal b { color: var(--sangria); }
	.caes li i { font-style: normal; font-size: .62rem; font-weight: 700; letter-spacing: .08em;
		text-transform: uppercase; border: 1.5px solid var(--sangria); color: var(--sangria);
		border-radius: 99px; padding: .05rem .45rem; flex: none; }

	.src { margin: 0; font-size: .74rem; color: var(--ink-faint); line-height: 1.5; max-width: 72ch; }

	/* skeleton stand-ins keep the same geometry as the markup they replace */
	.sk-dl { display: grid; grid-template-columns: max-content minmax(0, 1fr);
		gap: .3rem .9rem; margin: 0 0 1rem; align-items: baseline; }
	.sk-caes { display: grid; gap: .35rem; margin: .4rem 0 1rem; }
</style>
