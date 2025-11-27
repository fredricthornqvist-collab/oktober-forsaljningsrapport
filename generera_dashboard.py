#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generera HTML Dashboard för Oktober-försäljning med Fortnox-styling
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def ladda_data(filpath):
    """Ladda och förbered datan från CSV-filen."""
    df = pd.read_csv(filpath)
    
    # Rensa och konvertera numeriska kolumner - ta bort mellanslag och non-breaking spaces
    numeriska_kolumner = ['Antal försäljningsordrar', 'Försäljning', 'Rabattvärde']
    for kol in numeriska_kolumner:
        # Konvertera till string först, sedan ta bort alla mellanslag (både vanliga och non-breaking)
        df[kol] = df[kol].astype(str).str.replace(' ', '').str.replace('\xa0', '')
        df[kol] = pd.to_numeric(df[kol], errors='coerce').fillna(0)
    
    # Separera år och månad från ÅrMånad-kolumnen
    df['År'] = df['ÅrMånad'] // 100
    df['Månad'] = df['ÅrMånad'] % 100
    
    # Beräkna ordervärde (försäljning + rabattvärde)
    df['Ordervärde'] = df['Försäljning'] + df['Rabattvärde']
    
    # Beräkna rabatt%
    df['Rabatt%'] = np.where(
        df['Ordervärde'] > 0,
        (df['Rabattvärde'] / df['Ordervärde']) * 100,
        0
    )
    
    return df


def filtrera_period(df, år, månad):
    """Filtrera data för en specifik period."""
    return df[(df['År'] == år) & (df['Månad'] == månad)].copy()


def beräkna_huvud_kpi(df):
    """Beräkna huvud-KPI:er för en given period."""
    return {
        'Ordervärde': df['Ordervärde'].sum(),
        'Försäljning': df['Försäljning'].sum(),
        'Rabattvärde': df['Rabattvärde'].sum(),
        'Försäljningsantal': df['Antal försäljningsordrar'].sum(),
        'Rabatt%': (df['Rabattvärde'].sum() / df['Ordervärde'].sum() * 100) if df['Ordervärde'].sum() > 0 else 0,
    }


def jämför_perioder(kpi_aktuell, kpi_jämförelse):
    """Jämför två perioder och returnera förändringarna."""
    jämförelse = {}
    
    for nyckel in ['Ordervärde', 'Försäljning', 'Rabattvärde', 'Försäljningsantal']:
        värde_aktuell = kpi_aktuell[nyckel]
        värde_jämförelse = kpi_jämförelse[nyckel]
        
        if värde_jämförelse > 0:
            förändring_procent = ((värde_aktuell - värde_jämförelse) / värde_jämförelse) * 100
        else:
            förändring_procent = 0 if värde_aktuell == 0 else 100
        
        jämförelse[nyckel] = {
            'Aktuell': värde_aktuell,
            'Jämförelse': värde_jämförelse,
            'Förändring%': förändring_procent,
        }
    
    # Rabatt% behandlas annorlunda
    jämförelse['Rabatt%'] = {
        'Aktuell': kpi_aktuell['Rabatt%'],
        'Jämförelse': kpi_jämförelse['Rabatt%'],
        'Förändring_pp': kpi_aktuell['Rabatt%'] - kpi_jämförelse['Rabatt%'],
    }
    
    return jämförelse


def analysera_dimension(df_aktuell, df_yoy_jämförelse, df_mom_jämförelse, dimension, top_n=10, exkludera_värden=None):
    """Analysera en specifik dimension med både YoY och MoM jämförelser."""
    
    # Filtrera bort oönskade värden om specificerat
    if exkludera_värden:
        df_aktuell = df_aktuell[~df_aktuell[dimension].isin(exkludera_värden)]
        df_yoy_jämförelse = df_yoy_jämförelse[~df_yoy_jämförelse[dimension].isin(exkludera_värden)]
        df_mom_jämförelse = df_mom_jämförelse[~df_mom_jämförelse[dimension].isin(exkludera_värden)]
    
    # Aggregera för aktuell period
    agg_aktuell = df_aktuell.groupby(dimension).agg({
        'Ordervärde': 'sum',
        'Antal försäljningsordrar': 'sum'
    }).reset_index()
    
    # Aggregera för YoY jämförelseperiod
    agg_yoy = df_yoy_jämförelse.groupby(dimension).agg({
        'Antal försäljningsordrar': 'sum'
    }).reset_index()
    
    # Aggregera för MoM jämförelseperiod
    agg_mom = df_mom_jämförelse.groupby(dimension).agg({
        'Antal försäljningsordrar': 'sum'
    }).reset_index()
    
    # Slå samman YoY
    jämförelse_df = pd.merge(
        agg_aktuell,
        agg_yoy,
        on=dimension,
        how='outer',
        suffixes=('_aktuell', '_yoy')
    ).fillna(0)
    
    # Slå samman MoM
    jämförelse_df = pd.merge(
        jämförelse_df,
        agg_mom,
        on=dimension,
        how='outer'
    ).fillna(0)
    
    # Rename MoM kolumn
    jämförelse_df = jämförelse_df.rename(columns={'Antal försäljningsordrar': 'Antal försäljningsordrar_mom'})
    
    # Sortera efter ordervärde aktuell period
    jämförelse_df = jämförelse_df.sort_values('Ordervärde', ascending=False)
    
    return jämförelse_df.head(top_n) if len(jämförelse_df) > top_n else jämförelse_df


def generera_kpi_card_kombinerad(titel, värde_aktuell, värde_yoy, värde_mom, förändring_yoy, förändring_mom, är_rabatt=False, månad=10, år=2025):
    """Generera HTML för ett kombinerat KPI-kort med både YoY och MoM."""
    
    # Månadsnamn
    månadsnamn = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Maj", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dec"
    }
    
    # Beräkna föregående månad för MoM-jämförelse
    if månad == 1:
        mom_månad = 12
        mom_år = år - 1
    else:
        mom_månad = månad - 1
        mom_år = år
    
    # YoY jämförelse (samma månad föregående år)
    yoy_år = år - 1
    
    if är_rabatt:
        värde_text = f"{värde_aktuell:.2f}%"
        yoy_text = f"vs {månadsnamn[månad]} {yoy_år}: {värde_yoy:.2f}%"
        mom_text = f"vs {månadsnamn[mom_månad]} {mom_år}: {värde_mom:.2f}%"
        yoy_förändring_text = f"{förändring_yoy:+.2f}pp"
        mom_förändring_text = f"{förändring_mom:+.2f}pp"
        yoy_positiv = förändring_yoy < 0  # Lägre rabatt är bättre
        mom_positiv = förändring_mom < 0
    else:
        if "värde" in titel.lower():
            värde_text = f"{värde_aktuell:,.0f} kr"
            yoy_text = f"vs {månadsnamn[månad]} {yoy_år}: {värde_yoy:,.0f} kr"
            mom_text = f"vs {månadsnamn[mom_månad]} {mom_år}: {värde_mom:,.0f} kr"
        else:
            värde_text = f"{int(värde_aktuell):,}"
            yoy_text = f"vs {månadsnamn[månad]} {yoy_år}: {int(värde_yoy):,}"
            mom_text = f"vs {månadsnamn[mom_månad]} {mom_år}: {int(värde_mom):,}"
        yoy_förändring_text = f"{förändring_yoy:+.1f}%"
        mom_förändring_text = f"{förändring_mom:+.1f}%"
        yoy_positiv = förändring_yoy > 0
        mom_positiv = förändring_mom > 0
    
    yoy_pil = "↑" if yoy_positiv else "↓" if not yoy_positiv and förändring_yoy != 0 else "→"
    yoy_färg = "positive" if yoy_positiv else "negative" if förändring_yoy != 0 else "neutral"
    
    mom_pil = "↑" if mom_positiv else "↓" if not mom_positiv and förändring_mom != 0 else "→"
    mom_färg = "positive" if mom_positiv else "negative" if förändring_mom != 0 else "neutral"
    
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{titel}</div>
        <div class="kpi-value">{värde_text}</div>
        <div class="kpi-comparisons">
            <div class="comparison-row">
                <span class="comparison-label">YoY:</span>
                <span class="comparison-value">{yoy_text}</span>
                <span class="kpi-change-inline {yoy_färg}">
                    <span class="arrow-small">{yoy_pil}</span>
                    {yoy_förändring_text}
                </span>
            </div>
            <div class="comparison-row">
                <span class="comparison-label">MoM:</span>
                <span class="comparison-value">{mom_text}</span>
                <span class="kpi-change-inline {mom_färg}">
                    <span class="arrow-small">{mom_pil}</span>
                    {mom_förändring_text}
                </span>
            </div>
        </div>
    </div>
    """


def generera_tabell(titel, df, dimension_namn, max_rader=10):
    """Generera HTML-tabell för dimensionsanalys."""
    
    # Begränsa antal rader
    df = df.head(max_rader)
    
    # Beräkna förändringar för både YoY och MoM
    df = df.copy()
    df['Antal_yoy_förändring%'] = np.where(
        df['Antal försäljningsordrar_yoy'] > 0,
        ((df['Antal försäljningsordrar_aktuell'] - df['Antal försäljningsordrar_yoy']) / 
         df['Antal försäljningsordrar_yoy']) * 100,
        0
    )
    
    df['Antal_mom_förändring%'] = np.where(
        df['Antal försäljningsordrar_mom'] > 0,
        ((df['Antal försäljningsordrar_aktuell'] - df['Antal försäljningsordrar_mom']) / 
         df['Antal försäljningsordrar_mom']) * 100,
        0
    )
    
    rader_html = ""
    for _, rad in df.iterrows():
        yoy_förändring = rad['Antal_yoy_förändring%']
        yoy_klass = "positive" if yoy_förändring > 0 else "negative" if yoy_förändring < 0 else "neutral"
        yoy_pil = "↑" if yoy_förändring > 0 else "↓" if yoy_förändring < 0 else "→"
        
        mom_förändring = rad['Antal_mom_förändring%']
        mom_klass = "positive" if mom_förändring > 0 else "negative" if mom_förändring < 0 else "neutral"
        mom_pil = "↑" if mom_förändring > 0 else "↓" if mom_förändring < 0 else "→"
        
        rader_html += f"""
        <tr>
            <td class="dimension-name">{rad[dimension_namn]}</td>
            <td class="number">{int(rad['Antal försäljningsordrar_aktuell']):,}</td>
            <td class="number {yoy_klass}">
                <span class="arrow-small">{yoy_pil}</span>
                {yoy_förändring:+.1f}%
            </td>
            <td class="number {mom_klass}">
                <span class="arrow-small">{mom_pil}</span>
                {mom_förändring:+.1f}%
            </td>
        </tr>
        """
    
    return f"""
    <div class="table-card">
        <h3>{titel}</h3>
        <table>
            <thead>
                <tr>
                    <th>{dimension_namn}</th>
                    <th>Antal</th>
                    <th>YoY %</th>
                    <th>MoM %</th>
                </tr>
            </thead>
            <tbody>
                {rader_html}
            </tbody>
        </table>
    </div>
    """


def generera_innehåll_för_filter(df, okt_2025, okt_2024, sep_2025, filter_namn):
    """Generera KPI och tabeller för ett specifikt filter."""
    # Beräkna KPI:er
    kpi_okt_2025 = beräkna_huvud_kpi(okt_2025)
    kpi_okt_2024 = beräkna_huvud_kpi(okt_2024)
    kpi_sep_2025 = beräkna_huvud_kpi(sep_2025)
    
    # Jämförelser
    yoy = jämför_perioder(kpi_okt_2025, kpi_okt_2024)
    mom = jämför_perioder(kpi_okt_2025, kpi_sep_2025)


def generera_innehåll_för_månad_och_kanal(df, månad, år=2025, säljkanal=None):
    """Generera KPI och tabeller för en specifik månad och säljkanal."""
    # Filtrera data baserat på säljkanal
    if säljkanal:
        df = df[df['SäljKanal'] == säljkanal]
    
    # Filtrera för aktuell månad
    aktuell_period = filtrera_period(df, år, månad)
    
    # Filtrera för YoY jämförelse (samma månad föregående år)
    yoy_period = filtrera_period(df, år - 1, månad)
    
    # Filtrera för MoM jämförelse (föregående månad)
    if månad == 1:
        # Januari jämför med december föregående år
        mom_period = filtrera_period(df, år - 1, 12)
    else:
        mom_period = filtrera_period(df, år, månad - 1)
    
    # Beräkna KPI:er
    kpi_aktuell = beräkna_huvud_kpi(aktuell_period)
    kpi_yoy = beräkna_huvud_kpi(yoy_period)
    kpi_mom = beräkna_huvud_kpi(mom_period)
    
    # Jämförelser
    yoy = jämför_perioder(kpi_aktuell, kpi_yoy)
    mom = jämför_perioder(kpi_aktuell, kpi_mom)
    
    # Generera kombinerade KPI-kort
    kpi_cards = f"""
        <div class="kpi-grid">
            {generera_kpi_card_kombinerad("Ordervärde", 
                kpi_aktuell['Ordervärde'], kpi_yoy['Ordervärde'], kpi_mom['Ordervärde'],
                yoy['Ordervärde']['Förändring%'], mom['Ordervärde']['Förändring%'], 
                månad=månad, år=år)}
            {generera_kpi_card_kombinerad("Försäljning", 
                kpi_aktuell['Försäljning'], kpi_yoy['Försäljning'], kpi_mom['Försäljning'],
                yoy['Försäljning']['Förändring%'], mom['Försäljning']['Förändring%'],
                månad=månad, år=år)}
            {generera_kpi_card_kombinerad("Försäljningsantal", 
                kpi_aktuell['Försäljningsantal'], kpi_yoy['Försäljningsantal'], kpi_mom['Försäljningsantal'],
                yoy['Försäljningsantal']['Förändring%'], mom['Försäljningsantal']['Förändring%'],
                månad=månad, år=år)}
            {generera_kpi_card_kombinerad("Rabatt%", 
                kpi_aktuell['Rabatt%'], kpi_yoy['Rabatt%'], kpi_mom['Rabatt%'],
                yoy['Rabatt%']['Förändring_pp'], mom['Rabatt%']['Förändring_pp'], 
                är_rabatt=True, månad=månad, år=år)}
        </div>
    """
    
    # Analysera dimensioner
    kampanj_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'KampanjKod', top_n=8, exkludera_värden=['Kod saknas'])
    anställda_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'Antal anställda', top_n=8)
    bolagsform_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'Bolagsform', top_n=5)
    kundtyp_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'Kundtyp', top_n=5)
    sni_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'SNI', top_n=10, exkludera_värden=['-'])
    
    # Generera tabeller (visa säljkanal endast om vi inte filtrerat på kanal)
    if säljkanal is None:
        säljkanal_analys = analysera_dimension(aktuell_period, yoy_period, mom_period, 'SäljKanal', top_n=5)
        säljkanal_tabell = generera_tabell("Säljkanaler", säljkanal_analys, 'SäljKanal', 5)
    else:
        säljkanal_tabell = ""
    
    tabeller = f"""
        <div class="tables-grid">
            {generera_tabell("Kundtyp", kundtyp_analys, 'Kundtyp', 5)}
            {säljkanal_tabell}
            {generera_tabell("Top Kampanjkoder", kampanj_analys, 'KampanjKod', 8)}
            {generera_tabell("Antal Anställda", anställda_analys, 'Antal anställda', 8)}
            {generera_tabell("Bolagsform", bolagsform_analys, 'Bolagsform', 5)}
            {generera_tabell("Top SNI-koder", sni_analys, 'SNI', 10)}
        </div>
    """
    
    return kpi_cards, tabeller


def generera_dashboard():
    """Huvudfunktion för att generera dashboard."""
    
    # Hitta CSV-filen
    csv_fil = Path(__file__).parent / "8520e6e8-926a-4264-b6ad-e545036fe730 - Sheet1.csv"
    
    # Ladda data
    df = ladda_data(csv_fil)
    
    # Definiera månader som finns i datan
    månader = [
        (1, "Januari"), (2, "Februari"), (3, "Mars"), (4, "April"),
        (5, "Maj"), (6, "Juni"), (7, "Juli"), (8, "Augusti"),
        (9, "September"), (10, "Oktober")
    ]
    
    # Definiera säljkanaler
    kanaler = [
        (None, "alla", "Alla kanaler"),
        ("Fortnox.Se", "fortnox-se", "Fortnox.Se"),
        ("Fortnox", "fortnox", "Fortnox (Säljare)")
    ]
    
    # Generera innehåll för alla kombinationer av månad och kanal
    månad_kanal_innehåll = {}
    for månad_nr, månad_namn in månader:
        for kanal_filter, kanal_id, kanal_visningsnamn in kanaler:
            kpi_cards, tabeller = generera_innehåll_för_månad_och_kanal(df, månad_nr, 2025, kanal_filter)
            månad_kanal_innehåll[f"{månad_nr}_{kanal_id}"] = {
                'kpi': kpi_cards,
                'tabeller': tabeller,
                'månad_namn': månad_namn,
                'kanal_namn': kanal_visningsnamn
            }
    
    # Bygg HTML-innehåll dynamiskt för alla månad-kanal kombinationer
    kpi_sections_html = ""
    table_sections_html = ""
    
    for månad_nr, månad_namn in månader:
        for kanal_filter, kanal_id, kanal_visningsnamn in kanaler:
            key = f"{månad_nr}_{kanal_id}"
            innehåll = månad_kanal_innehåll[key]
            
            # Standard: visa oktober + alla kanaler, dölj resten
            display = "block" if månad_nr == 10 and kanal_id == "alla" else "none"
            
            # KPI-sektion
            kpi_sections_html += f"""
        <!-- KPI-sektion för {månad_namn} - {kanal_visningsnamn} -->
        <div class="section" id="kpi-{månad_nr}-{kanal_id}" data-month="{månad_nr}" data-channel="{kanal_id}" style="display: {display};">
            <div class="section-header">
                <h2>Nyckeltal {månad_namn} 2025{'' if kanal_id == 'alla' else ' - ' + kanal_visningsnamn}</h2>
                <p class="subtitle">Jämförelser Year-over-Year & Month-over-Month</p>
            </div>
            {innehåll['kpi']}
        </div>
        """
            
            # Tabell-sektion
            table_sections_html += f"""
        <!-- Detaljerad analys för {månad_namn} - {kanal_visningsnamn} -->
        <div class="section" id="tabeller-{månad_nr}-{kanal_id}" data-month="{månad_nr}" data-channel="{kanal_id}" style="display: {display};">
            <div class="section-header">
                <h2>Detaljerad Analys{'' if kanal_id == 'alla' else ' - ' + kanal_visningsnamn}</h2>
                <p class="subtitle">Top-prestationer och trender per dimension</p>
            </div>
            {innehåll['tabeller']}
        </div>
        """
    
    # Skapa HTML-dokument
    html_content = f"""
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
    <meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet">
    <meta http-equiv="X-Robots-Tag" content="noindex, nofollow, noarchive, nosnippet">
    <title>Försäljningsrapport 2025 - Fortnox</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            /* Fortnox färgpalett */
            --fortnox-green: #00B888;
            --fortnox-dark-green: #00976F;
            --fortnox-light-green: #E6F7F3;
            --fortnox-navy: #0A2540;
            --fortnox-dark-navy: #001428;
            --fortnox-gray: #6B7280;
            --fortnox-light-gray: #F3F4F6;
            --fortnox-border: #E5E7EB;
            
            /* Status färger */
            --color-positive: #10B981;
            --color-negative: #EF4444;
            --color-neutral: #6B7280;
            
            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: var(--fortnox-navy);
            line-height: 1.6;
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 2rem 2.5rem;
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            border-left: 6px solid var(--fortnox-green);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--fortnox-navy);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .header h1::before {{
            content: '';
            display: inline-block;
            width: 8px;
            height: 40px;
            background: var(--fortnox-green);
            border-radius: 4px;
        }}
        
        .header-meta {{
            color: var(--fortnox-gray);
            font-size: 1rem;
            margin-top: 0.5rem;
        }}
        
        .section {{
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            margin-bottom: 2rem;
        }}
        
        .section-header {{
            margin-bottom: 2rem;
        }}
        
        .section-header h2 {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--fortnox-navy);
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--fortnox-gray);
            font-size: 0.95rem;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
            padding: 1.75rem;
            border-radius: 12px;
            border: 2px solid var(--fortnox-border);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--fortnox-green), var(--fortnox-dark-green));
        }}
        
        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--fortnox-green);
        }}
        
        .kpi-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--fortnox-gray);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.75rem;
        }}
        
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--fortnox-navy);
            margin-bottom: 1rem;
            font-variant-numeric: tabular-nums;
        }}
        
        .kpi-comparisons {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .comparison-row {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
        }}
        
        .comparison-label {{
            font-weight: 600;
            color: var(--fortnox-navy);
            min-width: 45px;
        }}
        
        .comparison-value {{
            color: var(--fortnox-gray);
            flex: 1;
            font-variant-numeric: tabular-nums;
        }}
        
        .kpi-change-inline {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            background: rgba(0, 0, 0, 0.03);
        }}
        
        .kpi-change-inline.positive {{
            color: var(--color-positive);
            background: rgba(16, 185, 129, 0.1);
        }}
        
        .kpi-change-inline.negative {{
            color: var(--color-negative);
            background: rgba(239, 68, 68, 0.1);
        }}
        
        .kpi-change-inline.neutral {{
            color: var(--color-neutral);
        }}
        
        .arrow-small {{
            font-size: 1rem;
            font-weight: bold;
        }}
        
        .tables-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
        }}
        
        .table-card {{
            background: white;
            border-radius: 12px;
            border: 2px solid var(--fortnox-border);
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .table-card:hover {{
            box-shadow: var(--shadow-lg);
            border-color: var(--fortnox-green);
        }}
        
        .table-card h3 {{
            background: linear-gradient(135deg, var(--fortnox-navy) 0%, var(--fortnox-dark-navy) 100%);
            color: white;
            padding: 1.25rem 1.5rem;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: var(--fortnox-light-gray);
        }}
        
        th {{
            text-align: left;
            padding: 1rem 1.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--fortnox-navy);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        th:nth-child(2),
        th:nth-child(3),
        th:nth-child(4) {{
            text-align: right;
        }}
        
        td {{
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--fortnox-border);
            font-size: 0.95rem;
        }}
        
        tbody tr {{
            transition: background-color 0.2s ease;
        }}
        
        tbody tr:hover {{
            background: var(--fortnox-light-green);
        }}
        
        .number {{
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }}
        
        .dimension-name {{
            font-weight: 500;
            color: var(--fortnox-navy);
        }}
        
        .positive {{
            color: var(--color-positive) !important;
        }}
        
        .negative {{
            color: var(--color-negative) !important;
        }}
        
        .neutral {{
            color: var(--color-neutral) !important;
        }}
        
        .arrow-small {{
            font-size: 1.1rem;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--fortnox-gray);
            font-size: 0.9rem;
        }}
        
        .footer a {{
            color: var(--fortnox-green);
            text-decoration: none;
            font-weight: 600;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 1.75rem;
            }}
            
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            
            .tables-grid {{
                grid-template-columns: 1fr;
            }}
            
            th, td {{
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
            }}
        }}
        
        @media print {{
            * {{
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
            }}
            
            body {{
                background: white !important;
                padding: 0;
                margin: 0;
            }}
            
            .container {{
                max-width: 100%;
                padding: 0;
            }}
            
            .header {{
                background: white !important;
                box-shadow: none !important;
                border-left: 6px solid var(--fortnox-green) !important;
                margin-bottom: 1.5rem;
                page-break-after: avoid;
            }}
            
            .header h1 {{
                font-size: 2rem;
                page-break-after: avoid;
            }}
            
            .section {{
                background: white !important;
                box-shadow: none !important;
                page-break-inside: avoid;
                margin-bottom: 1.5rem;
                border: 1px solid var(--fortnox-border);
                border-radius: 8px;
            }}
            
            .section-header {{
                page-break-after: avoid;
            }}
            
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem;
                page-break-inside: avoid;
            }}
            
            .kpi-card {{
                background: white !important;
                border: 2px solid var(--fortnox-border) !important;
                box-shadow: none !important;
                page-break-inside: avoid;
                padding: 1.25rem;
            }}
            
            .kpi-card::before {{
                background: linear-gradient(90deg, var(--fortnox-green), var(--fortnox-dark-green)) !important;
            }}
            
            .kpi-change-inline.positive {{
                background: rgba(16, 185, 129, 0.15) !important;
            }}
            
            .kpi-change-inline.negative {{
                background: rgba(239, 68, 68, 0.15) !important;
            }}
            
            .tables-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
                page-break-inside: avoid;
            }}
            
            .table-card {{
                background: white !important;
                border: 2px solid var(--fortnox-border) !important;
                box-shadow: none !important;
                page-break-inside: avoid;
                margin-bottom: 1rem;
            }}
            
            .table-card h3 {{
                background: linear-gradient(135deg, var(--fortnox-navy) 0%, var(--fortnox-dark-navy) 100%) !important;
                -webkit-print-color-adjust: exact !important;
                color: white !important;
                padding: 1rem 1.25rem;
                font-size: 1rem;
            }}
            
            table {{
                page-break-inside: auto;
            }}
            
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            
            thead {{
                display: table-header-group;
                background: var(--fortnox-light-gray) !important;
            }}
            
            tbody tr:hover {{
                background: transparent !important;
            }}
            
            th, td {{
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
            }}
            
            .footer {{
                page-break-before: avoid;
                padding: 1rem;
                font-size: 0.85rem;
            }}
            
            /* Färger måste bevaras i print */
            .positive {{
                color: var(--color-positive) !important;
            }}
            
            .negative {{
                color: var(--color-negative) !important;
            }}
            
            .neutral {{
                color: var(--color-neutral) !important;
            }}
        }}
        
        /* Lösenordsskydd styling */
        .login-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0A2540 0%, #00B888 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        
        .login-box {{
            background: white;
            padding: 3rem;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 90%;
            text-align: center;
        }}
        
        .login-box h2 {{
            color: var(--fortnox-navy);
            margin-bottom: 0.5rem;
            font-size: 1.75rem;
        }}
        
        .login-box p {{
            color: var(--fortnox-gray);
            margin-bottom: 2rem;
            font-size: 0.95rem;
        }}
        
        .login-input {{
            width: 100%;
            padding: 1rem;
            border: 2px solid var(--fortnox-border);
            border-radius: 8px;
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            margin-bottom: 1rem;
            transition: border-color 0.3s ease;
        }}
        
        .login-input:focus {{
            outline: none;
            border-color: var(--fortnox-green);
        }}
        
        .login-button {{
            width: 100%;
            padding: 1rem;
            background: var(--fortnox-green);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            transition: background 0.3s ease;
        }}
        
        .login-button:hover {{
            background: #009670;
        }}
        
        .login-error {{
            color: var(--color-negative);
            margin-top: 1rem;
            font-size: 0.9rem;
            display: none;
        }}
        
        .content-hidden {{
            display: none;
        }}
        
        /* Filter-knappar styling */
        .filter-section {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .filter-label {{
            color: var(--fortnox-navy);
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 1rem;
            display: block;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .filter-button {{
            padding: 0.75rem 2rem;
            border: 2px solid var(--fortnox-border);
            background: white;
            color: var(--fortnox-navy);
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
        }}
        
        .filter-button:hover {{
            border-color: var(--fortnox-green);
            color: var(--fortnox-green);
        }}
        
        .filter-button.active {{
            background: var(--fortnox-green);
            color: white;
            border-color: var(--fortnox-green);
        }}
    </style>
    <script>
        // Lösenordsskydd
        const CORRECT_PASSWORD = 'fortnoxftw2025';
        
        function checkPassword() {{
            const input = document.getElementById('passwordInput');
            const error = document.getElementById('loginError');
            const overlay = document.getElementById('loginOverlay');
            const content = document.getElementById('mainContent');
            
            if (input.value === CORRECT_PASSWORD) {{
                overlay.style.display = 'none';
                content.classList.remove('content-hidden');
                // Spara i sessionStorage så användaren inte behöver logga in igen under sessionen
                sessionStorage.setItem('authenticated', 'true');
            }} else {{
                error.style.display = 'block';
                input.value = '';
                input.focus();
            }}
        }}
        
        // Kolla om användaren redan är autentiserad
        window.addEventListener('DOMContentLoaded', function() {{
            if (sessionStorage.getItem('authenticated') === 'true') {{
                document.getElementById('loginOverlay').style.display = 'none';
                document.getElementById('mainContent').classList.remove('content-hidden');
            }}
        }});
        
        // Tillåt Enter-tangent för att logga in
        document.addEventListener('DOMContentLoaded', function() {{
            const input = document.getElementById('passwordInput');
            if (input) {{
                input.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        checkPassword();
                    }}
                }});
            }}
        }});
    </script>
</head>
<body>
    <!-- Lösenordsskydd overlay -->
    <div id="loginOverlay" class="login-overlay">
        <div class="login-box">
            <h2>🔒 Skyddad Rapport</h2>
            <p>Ange lösenord för att visa försäljningsrapporten</p>
            <input 
                type="password" 
                id="passwordInput" 
                class="login-input" 
                placeholder="Ange lösenord"
                autocomplete="off"
            >
            <button class="login-button" onclick="checkPassword()">Lås upp</button>
            <div id="loginError" class="login-error">❌ Felaktigt lösenord. Försök igen.</div>
        </div>
    </div>
    
    <!-- Huvudinnehåll (dolt tills rätt lösenord anges) -->
    <div id="mainContent" class="content-hidden">
    <div class="container">
        <div class="header">
            <h1>📊 Försäljningsrapport 2025</h1>
            <div class="header-meta">
                Genererad: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
                <span id="current-period">Oktober 2025</span> | 
                Jämförelser: YoY & MoM
            </div>
        </div>
        
        <!-- Månadsfilter -->
        <div class="filter-section">
            <span class="filter-label">Välj månad:</span>
            <div class="filter-buttons">
                <button class="filter-button" onclick="switchMonth(1)" data-month="1">Januari</button>
                <button class="filter-button" onclick="switchMonth(2)" data-month="2">Februari</button>
                <button class="filter-button" onclick="switchMonth(3)" data-month="3">Mars</button>
                <button class="filter-button" onclick="switchMonth(4)" data-month="4">April</button>
                <button class="filter-button" onclick="switchMonth(5)" data-month="5">Maj</button>
                <button class="filter-button" onclick="switchMonth(6)" data-month="6">Juni</button>
                <button class="filter-button" onclick="switchMonth(7)" data-month="7">Juli</button>
                <button class="filter-button" onclick="switchMonth(8)" data-month="8">Augusti</button>
                <button class="filter-button" onclick="switchMonth(9)" data-month="9">September</button>
                <button class="filter-button active" onclick="switchMonth(10)" data-month="10">Oktober</button>
            </div>
        </div>
        
        <!-- Säljkanalsfilter -->
        <div class="filter-section">
            <span class="filter-label">Filtrera på säljkanal:</span>
            <div class="filter-buttons">
                <button class="filter-button active" onclick="switchChannel('alla')" data-channel="alla">
                    📊 Alla kanaler
                </button>
                <button class="filter-button" onclick="switchChannel('fortnox-se')" data-channel="fortnox-se">
                    🌐 Fortnox.Se
                </button>
                <button class="filter-button" onclick="switchChannel('fortnox')" data-channel="fortnox">
                    👤 Fortnox (Säljare)
                </button>
            </div>
        </div>
        
        <!-- KPI-sektioner (genererade dynamiskt) -->
        {kpi_sections_html}
        
        <!-- Tabell-sektioner (genererade dynamiskt) -->
        {table_sections_html}
        
        <div class="footer">
            <p>Rapport genererad med Fortnox Analytics Tool</p>
            <p>© {datetime.now().year} Fortnox AB. Alla rättigheter förbehållna.</p>
        </div>
    </div>
    </div> <!-- Stäng mainContent div -->
    
    <script>
        // Håll reda på aktuell månad och kanal
        let currentMonth = 10;
        let currentChannel = 'alla';
        
        // Månadsnamn för visning
        const monthNames = {{
            1: 'Januari', 2: 'Februari', 3: 'Mars', 4: 'April',
            5: 'Maj', 6: 'Juni', 7: 'Juli', 8: 'Augusti',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'December'
        }};
        
        // Funktion för att uppdatera period-text
        function updatePeriodText() {{
            document.getElementById('current-period').textContent = monthNames[currentMonth] + ' 2025';
        }}
        
        // Funktion för att växla månad
        function switchMonth(month) {{
            currentMonth = month;
            
            // Uppdatera aktiv månadsknapp
            document.querySelectorAll('[data-month]').forEach(btn => {{
                if (btn.hasAttribute('onclick')) {{ // Endast månadsfilter-knappar
                    btn.classList.remove('active');
                }}
            }});
            document.querySelector(`[data-month="${{month}}"][onclick*="switchMonth"]`).classList.add('active');
            
            // Uppdatera period-text
            updatePeriodText();
            
            // Visa rätt innehåll
            showContent();
        }}
        
        // Funktion för att växla kanal
        function switchChannel(channel) {{
            currentChannel = channel;
            
            // Uppdatera aktiv kanalknapp
            document.querySelectorAll('[data-channel][onclick*="switchChannel"]').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector(`[data-channel="${{channel}}"][onclick*="switchChannel"]`).classList.add('active');
            
            // Visa rätt innehåll
            showContent();
        }}
        
        // Funktion för att visa rätt innehåll baserat på månad och kanal
        function showContent() {{
            // Dölj allt innehåll
            document.querySelectorAll('[data-month][data-channel]').forEach(section => {{
                section.style.display = 'none';
            }});
            
            // Visa innehåll för vald månad och kanal
            document.querySelectorAll(`[data-month="${{currentMonth}}"][data-channel="${{currentChannel}}"]`).forEach(section => {{
                section.style.display = 'block';
            }});
        }}
    </script>
</body>
</html>
    """
    
    # Spara HTML-filen
    output_fil = Path(__file__).parent / "oktober_dashboard.html"
    with open(output_fil, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Dashboard genererad framgångsrikt!")
    print(f"📄 Fil: {output_fil}")
    print(f"\n🌐 Öppna filen i din webbläsare för att se dashboarden.")
    
    return output_fil


if __name__ == "__main__":
    generera_dashboard()
