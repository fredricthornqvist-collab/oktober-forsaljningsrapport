#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analysverktyg för Oktober-försäljning
Jämför oktober 2025 vs oktober 2024 (YoY) och vs september 2025 (MoM)
"""

import pandas as pd
import numpy as np
from pathlib import Path


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
        'Antal_rader': len(df)
    }


def jämför_perioder(kpi_aktuell, kpi_jämförelse, period_namn):
    """Jämför två perioder och returnera förändringarna."""
    jämförelse = {}
    
    for nyckel in ['Ordervärde', 'Försäljning', 'Rabattvärde', 'Försäljningsantal', 'Rabatt%']:
        värde_aktuell = kpi_aktuell[nyckel]
        värde_jämförelse = kpi_jämförelse[nyckel]
        
        if nyckel == 'Rabatt%':
            # För procentenheter använder vi absolut skillnad
            skillnad = värde_aktuell - värde_jämförelse
            jämförelse[nyckel] = {
                'Aktuell': värde_aktuell,
                'Jämförelse': värde_jämförelse,
                'Skillnad_pp': skillnad,
                'Förändring': 'Bättre' if skillnad < 0 else ('Sämre' if skillnad > 0 else 'Oförändrat')
            }
        else:
            # För övriga värden beräknar vi procentuell förändring
            if värde_jämförelse > 0:
                förändring_procent = ((värde_aktuell - värde_jämförelse) / värde_jämförelse) * 100
            else:
                förändring_procent = 0 if värde_aktuell == 0 else float('inf')
            
            jämförelse[nyckel] = {
                'Aktuell': värde_aktuell,
                'Jämförelse': värde_jämförelse,
                'Skillnad': värde_aktuell - värde_jämförelse,
                'Förändring%': förändring_procent,
                'Förändring': 'Bättre' if förändring_procent > 0 else ('Sämre' if förändring_procent < 0 else 'Oförändrat')
            }
    
    return jämförelse


def analysera_dimension(df_aktuell, df_jämförelse, dimension, top_n=10):
    """Analysera en specifik dimension (t.ex. kampanjkod, säljkanal)."""
    
    # Aggregera för aktuell period
    agg_aktuell = df_aktuell.groupby(dimension).agg({
        'Ordervärde': 'sum',
        'Försäljning': 'sum',
        'Rabattvärde': 'sum',
        'Antal försäljningsordrar': 'sum'
    }).reset_index()
    
    # Aggregera för jämförelseperiod
    agg_jämförelse = df_jämförelse.groupby(dimension).agg({
        'Ordervärde': 'sum',
        'Försäljning': 'sum',
        'Rabattvärde': 'sum',
        'Antal försäljningsordrar': 'sum'
    }).reset_index()
    
    # Slå samman
    jämförelse_df = pd.merge(
        agg_aktuell,
        agg_jämförelse,
        on=dimension,
        how='outer',
        suffixes=('_aktuell', '_jämförelse')
    ).fillna(0)
    
    # Beräkna förändringar
    jämförelse_df['Ordervärde_förändring%'] = np.where(
        jämförelse_df['Ordervärde_jämförelse'] > 0,
        ((jämförelse_df['Ordervärde_aktuell'] - jämförelse_df['Ordervärde_jämförelse']) / 
         jämförelse_df['Ordervärde_jämförelse']) * 100,
        0
    )
    
    jämförelse_df['Försäljningsantal_förändring%'] = np.where(
        jämförelse_df['Antal försäljningsordrar_jämförelse'] > 0,
        ((jämförelse_df['Antal försäljningsordrar_aktuell'] - 
          jämförelse_df['Antal försäljningsordrar_jämförelse']) / 
         jämförelse_df['Antal försäljningsordrar_jämförelse']) * 100,
        0
    )
    
    # Beräkna rabatt%
    jämförelse_df['Rabatt%_aktuell'] = np.where(
        jämförelse_df['Ordervärde_aktuell'] > 0,
        (jämförelse_df['Rabattvärde_aktuell'] / jämförelse_df['Ordervärde_aktuell']) * 100,
        0
    )
    
    jämförelse_df['Rabatt%_jämförelse'] = np.where(
        jämförelse_df['Ordervärde_jämförelse'] > 0,
        (jämförelse_df['Rabattvärde_jämförelse'] / jämförelse_df['Ordervärde_jämförelse']) * 100,
        0
    )
    
    jämförelse_df['Rabatt%_förändring_pp'] = (
        jämförelse_df['Rabatt%_aktuell'] - jämförelse_df['Rabatt%_jämförelse']
    )
    
    # Sortera efter ordervärde aktuell period
    jämförelse_df = jämförelse_df.sort_values('Ordervärde_aktuell', ascending=False)
    
    # Returnera top N (eller alla om färre än top_n)
    return jämförelse_df.head(top_n) if len(jämförelse_df) > top_n else jämförelse_df


def skriv_rapport_huvud_kpi(titel, jämförelse):
    """Skriv ut en rapport för huvud-KPI:er."""
    print(f"\n{'='*80}")
    print(f"{titel}")
    print(f"{'='*80}\n")
    
    print(f"{'KPI':<25} {'Aktuell':>15} {'Jämförelse':>15} {'Förändring':>15} {'Status':>10}")
    print("-" * 80)
    
    for nyckel in ['Ordervärde', 'Försäljning', 'Rabattvärde', 'Försäljningsantal']:
        data = jämförelse[nyckel]
        if nyckel == 'Försäljningsantal':
            print(f"{nyckel:<25} {data['Aktuell']:>15,.0f} {data['Jämförelse']:>15,.0f} "
                  f"{data['Förändring%']:>14.1f}% {data['Förändring']:>10}")
        else:
            print(f"{nyckel:<25} {data['Aktuell']:>15,.0f} {data['Jämförelse']:>15,.0f} "
                  f"{data['Förändring%']:>14.1f}% {data['Förändring']:>10}")
    
    # Rabatt% visas annorlunda
    data = jämförelse['Rabatt%']
    print(f"{'Rabatt%':<25} {data['Aktuell']:>14.2f}% {data['Jämförelse']:>14.2f}% "
          f"{data['Skillnad_pp']:>14.2f}pp {data['Förändring']:>10}")


def skriv_rapport_dimension(titel, dimension_df, dimension_namn):
    """Skriv ut en rapport för en dimension."""
    print(f"\n{'='*100}")
    print(f"{titel}")
    print(f"{'='*100}\n")
    
    if len(dimension_df) == 0:
        print("Ingen data tillgänglig.")
        return
    
    print(f"{dimension_namn:<30} {'Ordervärde':>15} {'Förändring%':>12} "
          f"{'Försäljning':>13} {'Förändring%':>12}")
    print("-" * 100)
    
    for _, rad in dimension_df.iterrows():
        print(f"{str(rad[dimension_namn]):<30} "
              f"{rad['Ordervärde_aktuell']:>15,.0f} "
              f"{rad['Ordervärde_förändring%']:>11.1f}% "
              f"{rad['Antal försäljningsordrar_aktuell']:>13,.0f} "
              f"{rad['Försäljningsantal_förändring%']:>11.1f}%")


def analysera_oktober():
    """Huvudfunktion för att analysera oktober-försäljning."""
    
    # Hitta CSV-filen
    csv_fil = Path(__file__).parent / "8520e6e8-926a-4264-b6ad-e545036fe730 - Sheet1.csv"
    
    print("\n" + "="*80)
    print("ANALYSRAPPORT: OKTOBER-FÖRSÄLJNING")
    print("="*80)
    
    # Ladda data
    print("\nLaddar data...")
    df = ladda_data(csv_fil)
    
    # Filtrera perioder
    okt_2025 = filtrera_period(df, 2025, 10)
    okt_2024 = filtrera_period(df, 2024, 10)
    sep_2025 = filtrera_period(df, 2025, 9)
    
    print(f"Oktober 2025: {len(okt_2025)} rader")
    print(f"Oktober 2024: {len(okt_2024)} rader")
    print(f"September 2025: {len(sep_2025)} rader")
    
    # ==================== HUVUD-KPI:ER ====================
    
    # Beräkna KPI:er
    kpi_okt_2025 = beräkna_huvud_kpi(okt_2025)
    kpi_okt_2024 = beräkna_huvud_kpi(okt_2024)
    kpi_sep_2025 = beräkna_huvud_kpi(sep_2025)
    
    # YoY-jämförelse
    yoy_jämförelse = jämför_perioder(kpi_okt_2025, kpi_okt_2024, "YoY")
    skriv_rapport_huvud_kpi("OKTOBER 2025 vs OKTOBER 2024 (YoY)", yoy_jämförelse)
    
    # MoM-jämförelse
    mom_jämförelse = jämför_perioder(kpi_okt_2025, kpi_sep_2025, "MoM")
    skriv_rapport_huvud_kpi("OKTOBER 2025 vs SEPTEMBER 2025 (MoM)", mom_jämförelse)
    
    # ==================== KAMPANJKODER ====================
    
    print("\n\n" + "="*80)
    print("KAMPANJKODER (TOP 10)")
    print("="*80)
    
    # YoY
    kampanj_yoy = analysera_dimension(okt_2025, okt_2024, 'KampanjKod', top_n=10)
    skriv_rapport_dimension("Kampanjkoder - Oktober 2025 vs Oktober 2024 (YoY)", 
                           kampanj_yoy, 'KampanjKod')
    
    # MoM
    kampanj_mom = analysera_dimension(okt_2025, sep_2025, 'KampanjKod', top_n=10)
    skriv_rapport_dimension("Kampanjkoder - Oktober 2025 vs September 2025 (MoM)", 
                           kampanj_mom, 'KampanjKod')
    
    # ==================== SÄLJKANAL ====================
    
    print("\n\n" + "="*80)
    print("SÄLJKANAL")
    print("="*80)
    
    säljkanal_yoy = analysera_dimension(okt_2025, okt_2024, 'SäljKanal', top_n=20)
    skriv_rapport_dimension("Säljkanal - Oktober 2025 vs Oktober 2024 (YoY)", 
                           säljkanal_yoy, 'SäljKanal')
    
    säljkanal_mom = analysera_dimension(okt_2025, sep_2025, 'SäljKanal', top_n=20)
    skriv_rapport_dimension("Säljkanal - Oktober 2025 vs September 2025 (MoM)", 
                           säljkanal_mom, 'SäljKanal')
    
    # ==================== ANTAL ANSTÄLLDA ====================
    
    print("\n\n" + "="*80)
    print("ANTAL ANSTÄLLDA")
    print("="*80)
    
    anställda_yoy = analysera_dimension(okt_2025, okt_2024, 'Antal anställda', top_n=20)
    skriv_rapport_dimension("Antal anställda - Oktober 2025 vs Oktober 2024 (YoY)", 
                           anställda_yoy, 'Antal anställda')
    
    anställda_mom = analysera_dimension(okt_2025, sep_2025, 'Antal anställda', top_n=20)
    skriv_rapport_dimension("Antal anställda - Oktober 2025 vs September 2025 (MoM)", 
                           anställda_mom, 'Antal anställda')
    
    # ==================== AVTALSPERIOD ====================
    
    print("\n\n" + "="*80)
    print("AVTALSPERIOD")
    print("="*80)
    
    avtal_yoy = analysera_dimension(okt_2025, okt_2024, 'Avtalsperiod', top_n=20)
    skriv_rapport_dimension("Avtalsperiod - Oktober 2025 vs Oktober 2024 (YoY)", 
                           avtal_yoy, 'Avtalsperiod')
    
    avtal_mom = analysera_dimension(okt_2025, sep_2025, 'Avtalsperiod', top_n=20)
    skriv_rapport_dimension("Avtalsperiod - Oktober 2025 vs September 2025 (MoM)", 
                           avtal_mom, 'Avtalsperiod')
    
    # ==================== BOLAGSFORM ====================
    
    print("\n\n" + "="*80)
    print("BOLAGSFORM")
    print("="*80)
    
    bolag_yoy = analysera_dimension(okt_2025, okt_2024, 'Bolagsform', top_n=20)
    skriv_rapport_dimension("Bolagsform - Oktober 2025 vs Oktober 2024 (YoY)", 
                           bolag_yoy, 'Bolagsform')
    
    bolag_mom = analysera_dimension(okt_2025, sep_2025, 'Bolagsform', top_n=20)
    skriv_rapport_dimension("Bolagsform - Oktober 2025 vs September 2025 (MoM)", 
                           bolag_mom, 'Bolagsform')
    
    # ==================== KUNDTYP ====================
    
    print("\n\n" + "="*80)
    print("KUNDTYP")
    print("="*80)
    
    kundtyp_yoy = analysera_dimension(okt_2025, okt_2024, 'Kundtyp', top_n=20)
    skriv_rapport_dimension("Kundtyp - Oktober 2025 vs Oktober 2024 (YoY)", 
                           kundtyp_yoy, 'Kundtyp')
    
    kundtyp_mom = analysera_dimension(okt_2025, sep_2025, 'Kundtyp', top_n=20)
    skriv_rapport_dimension("Kundtyp - Oktober 2025 vs September 2025 (MoM)", 
                           kundtyp_mom, 'Kundtyp')
    
    # ==================== SNI ====================
    
    print("\n\n" + "="*80)
    print("SNI (TOP 15)")
    print("="*80)
    
    sni_yoy = analysera_dimension(okt_2025, okt_2024, 'SNI', top_n=15)
    skriv_rapport_dimension("SNI - Oktober 2025 vs Oktober 2024 (YoY)", 
                           sni_yoy, 'SNI')
    
    sni_mom = analysera_dimension(okt_2025, sep_2025, 'SNI', top_n=15)
    skriv_rapport_dimension("SNI - Oktober 2025 vs September 2025 (MoM)", 
                           sni_mom, 'SNI')
    
    # ==================== SAMMANFATTNING ====================
    
    print("\n\n" + "="*80)
    print("SAMMANFATTNING OCH INSIKTER")
    print("="*80)
    
    print("\n📊 HUVUD-KPI:ER - VAD HAR BLIVIT BÄTTRE/SÄMRE?")
    print("-" * 80)
    
    print("\nYear-over-Year (Oktober 2025 vs Oktober 2024):")
    for kpi in ['Ordervärde', 'Försäljningsantal', 'Rabatt%']:
        data = yoy_jämförelse[kpi]
        if kpi == 'Rabatt%':
            print(f"  • {kpi}: {data['Skillnad_pp']:+.2f}pp - {data['Förändring']}")
        else:
            print(f"  • {kpi}: {data['Förändring%']:+.1f}% - {data['Förändring']}")
    
    print("\nMonth-over-Month (Oktober 2025 vs September 2025):")
    for kpi in ['Ordervärde', 'Försäljningsantal', 'Rabatt%']:
        data = mom_jämförelse[kpi]
        if kpi == 'Rabatt%':
            print(f"  • {kpi}: {data['Skillnad_pp']:+.2f}pp - {data['Förändring']}")
        else:
            print(f"  • {kpi}: {data['Förändring%']:+.1f}% - {data['Förändring']}")
    
    print("\n\n✅ ANALYS SLUTFÖRD!")
    print("="*80)


if __name__ == "__main__":
    analysera_oktober()
