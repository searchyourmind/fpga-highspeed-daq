"""Check numerical evidence without converting failed design margins to PASS."""
from pathlib import Path
import json,hashlib,datetime
R=Path(__file__).resolve().parents[3];H=R/'hardware/reference_pcie_adapter';O=H/'outputs/engineering'
def read(n):return json.loads((O/(n+'.json')).read_text())
field=read('field-solver');mech=read('mechanical');si=read('si-return-paths');dc=read('dc-network');thermal=read('thermal');power=read('power-corners');tran=read('adapter-transient');bom=read('component-selection');cad=json.loads((H/'outputs/check-summary.json').read_text())
loaded=read('adapter-loaded-corner'); feasibility=read('voltage-feasibility'); width=read('si-width-feasibility'); mitigation=read('thermal-exit-requirement')
checks={
 'loaded_corner_trace_completed':loaded['status']=='PASS_MODEL_CHECKS' and loaded['raw_points']==6455898 and all(loaded['checks'].values()),
 'loaded_source_matches_recorded_run':loaded['source_sha256']==hashlib.sha256((H/'analysis/adapter_loaded_corner.cir').read_bytes()).hexdigest(),
 'dynamic_reserve_covers_executed_corner_regulator_excursion':loaded['existing_40mV_reserve_margin_V']>=0,
 'original_SI_width_candidates_executed':len(width['candidates'])==4,
 'thermal_mitigation_not_mistaken_for_implemented_hardware':mitigation['status']=='CANDIDATE_REQUIREMENT_NOT_IMPLEMENTED' and max(x['energy_balance_relative_error'] for x in mitigation['cases'])<1e-8,
 'divider_feasibility_preserves_requirements':not feasibility['requirements_relaxed'] and not feasibility['divider_only_solution_exists'],
 'DC_graph_independent_analytic_fixtures':read('dc-analytic-tests')['status']=='PASS',
 'cad_erc_drc_parity_connectivity':cad['cad_checks']=='PASS' and not cad['fabrication_released'],
 'all_30_electrical_refs_in_engineering_BOM':len(bom['components'])==30 and len({x['reference'] for x in bom['components']})==30,
 'mechanical_2D_envelope':mech['status']=='PASS_2D',
 'no_unintended_reference_voids_and_return_vias_within_1mm':si['status']=='PASS_GEOMETRY',
 'field_residual_energy_mesh_domain_and_homogeneous_check':field['status']=='PASS_NUMERICS' and field['mesh_last_relative_change']<.035 and field['domain_relative_change']<.02 and abs(field['homogeneous_epsilon_check']-4)<1e-9,
 'DC_network_all_126_distributions_and_KCL':dc['output']['load_distribution_corners']==126 and max(dc[n]['max_kcl_residual_A'] for n in ('output','input'))<1e-8,
 'power_core_108_DC_AC_sweeps':len(power['cases'])==108 and all(c['status']=='PASS_DC_AND_FINITE_AC' and c['ac_points']==121 for c in power['cases']),
 'A_model_transient':tran['status']=='PASS_MODEL_CHECKS' and all(tran['checks'].values()),
 'transient_source_matches_recorded_run':tran['source_sha256']==hashlib.sha256((H/'analysis/adapter_transient.cir').read_bytes()).hexdigest(),
 'thermal_24_cases_energy_and_mesh':len(thermal['cases'])==24 and max(c['energy_balance_relative_error'] for c in thermal['cases'])<1e-8 and thermal['mesh_last_delta_T_C']<2,
 'thermal_copper_loss_covers_DC_network_at125C':min(c['assumed_copper_loss_W'] for c in thermal['cases'])>=sum(dc[n]['worst_distribution_2A']['loss_W'] for n in ('input','output')),
 'nominal_transient_reserve_covers_observed_peak':power['budget']['explicit_unverified_reserves']['ripple_transient_peak_V']>=max(abs(tran['windows']['load_step'][k]-tran['windows']['pre_step']['time_weighted_mean_V']) for k in ('min_V','max_V')),
}
# Independent minimum-copper/profile review is optional during the legacy full chain,
# but once present it is validated and must not inherit the old nominal-copper PASS.
independent=(O/'thermal-independent-review.json').exists() and (O/'si-independent-review.json').exists() and (O/'voltage-root-cause.json').exists()
if independent:
 it=read('thermal-independent-review');iz=read('si-independent-review');iv=read('voltage-root-cause')
 checks.update({
  'independent_thermal_exact_fixture_and_superposition':it['uniform_source_exact_solution_error_C']<1e-8 and it['superposition_max_error_C']<1e-8,
  'minimum_copper_24case_and_hot_refinement':len(it['corrected_minimum_outer_copper_cases'])==24 and it['corrected_failing_count']==6 and it['worst_corrected_mesh_delta_C']<.5 and it['case3_corrected_fine']['estimated_regulator_junction_C']>125,
  'expanded_SI_31_solves_original_baseline_and_failed_candidate':len(iz['sensitivity_cases'])==31 and iz['legacy_unchanged'] and min(x['Zdiff_ohm'] for x in iz['sensitivity_cases'] if 'candidate7628' in x['case'])<81,
  'voltage_root_cause_preserves_failed_margins':iv['status']=='FAIL_REQUIREMENTS' and all(x['margin_mV']<0 for x in iv['cases']),
 })
result={'independent_review_included':independent,'revision':'0.3.1','checked_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'software_evidence_checks':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'design_gates':{'worst_case_voltage_budget':'PASS' if power['budget']['tolerance_budget_pass'] else 'FAIL_MARGIN','thermal_all_screened_environments':'PASS' if all(c['within_125C'] for c in thermal['cases']) else 'CONDITIONAL_FAIL_HOT_WEAK_CONVECTION','SI_broad_assumed_process_corners':'PASS' if field['all_screened_corners_in_target'] else 'FAIL_MARGIN','BOM_cable_SSD_assembly':'REVIEW_REQUIRED','fabrication_released':False},'input_sha256':{p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list((H/'analysis').glob('*.py'))+list((H/'analysis').glob('*.cir'))+[p for p in (H/'kicad').glob('*.kicad_*') if p.suffix!='.kicad_prl']+[H/'routing/tracks.json',H/'BOM_selected.csv'])}}
if independent:
 result['design_gates']['minimum_copper_thermal_failures']=it['corrected_failing_count']
 result['design_gates']['minimum_copper_fine_worst_Tj_C']=it['worst_corrected_fine']['estimated_regulator_junction_C']
 result['design_gates']['thermal_all_screened_environments']='FAIL_MARGIN'
(R/'results').mkdir(parents=True,exist_ok=True)
(R/'results/engineering-check-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(checks.values()),checks
