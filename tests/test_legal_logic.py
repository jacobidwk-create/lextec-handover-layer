"""Legal prerequisite regression cases; no model or external delivery."""
from datetime import date
import pytest
from handover.areas import required_fields, FIELD_BY_NAME, WHY, LABELS
from handover.schema import Case, Fact, Status, Route
from handover.rules import gate
from handover.deadlines import compute_deadlines
from handover.legal_logic import legal_context

TODAY = date(2026, 11, 12)
COMMON = dict(jurisdiction='zurich', case_complexity=False, other_official_deadline=False)
# Late fees: private letter, in default after a reminder, three charges answered.
DEBT = dict(document_type='reminder', claim_amount=400, principal_status='open',
            default_trigger='reminder', interest_charge='statutory',
            reminder_fee='not_agreed', collection_costs='flat')
# Declining an inheritance: statutory heir, period open, nothing touched, estate over-indebted.
ESTATE = dict(heir_basis='statutory', date_learned_of_death=date(2026,11,1),
              estate_actions='none', estate_finances='overindebted')
# Register entry: enforcement not paid, objection raised, three months over, creditor silent.
REGISTER = dict(register_entry='enforcement', register_payment='not_paid',
                register_objection='yes', register_service_date=date(2026,5,1),
                register_creditor_step='none')


def make(area, values):
    c=Case(areas={area:'user statement'})
    c.facts={k:Fact(k,Status.KNOWN,v,'explicit user statement') for k,v in {**COMMON,**values}.items()}
    return c


@pytest.mark.parametrize('area,values', [('debt_collection',DEBT),('inheritance_debt',ESTATE),('credit_record',REGISTER)])
def test_complete_ordinary_branch_and_each_missing_prerequisite(area,values):
    c=make(area,values)
    assert gate(c,TODAY).route is Route.PROCEED
    for spec in required_fields(c):
        candidate=make(area,values)
        candidate.facts.pop(spec.name,None)
        assert gate(candidate,TODAY).route is not Route.PROCEED, spec.name
        candidate.facts[spec.name]=Fact(spec.name,Status.USER_UNKNOWN)
        # A fact that decides the route fails closed. The three charges of the late-fee
        # framework (gate 3) do not decide the route: "I do not know" gives a
        # conditional text instead (test_late_fees.py), never a yes or a no.
        # "I do not know" about dealings with the estate leads to a hand-over proposal;
        # about the estate's finances it counts as "uncertain" (test_inheritance.py).
        expected=Route.REFER if spec.critical or spec.name=='estate_actions' else Route.PROCEED
        assert gate(candidate,TODAY).route is expected, spec.name
        # No answer of the register flow decides the route alone (test_register.py).
        assert spec.critical or spec.area in ('debt_collection','inheritance_debt','credit_record'), spec.name


def test_amount_is_not_asked_but_a_stated_high_amount_still_refers():
    c=make('debt_collection',DEBT)
    assert 'claim_amount' not in {x.name for x in required_fields(c)}
    c.facts['claim_amount']=Fact('claim_amount',Status.USER_UNKNOWN)
    assert gate(c,TODAY).route is Route.PROCEED
    c.facts['claim_amount']=Fact('claim_amount',Status.KNOWN,9000.0,'9000 Franken')
    d=gate(c,TODAY)
    assert d.route is Route.REFER and not d.urgent
    assert [r.rule for r in d.reasons]==['R5-high-amount']


def test_old_short_register_questionnaire_is_insufficient():
    c=make('credit_record',dict(record_holder='enforcement_register',register_debt_status='disputed'))
    assert gate(c,TODAY).route is Route.ASK


def payment(**changes):
    return make('debt_collection',{**DEBT,'document_type':'payment_order',
        'document_received_date':date(2026,11,3),'service_disputed':False,
        'objection_filed':True,'objection_date':date(2026,11,4),
        'objection_recipient':'office','objection_scope':'full',**changes})


def test_objection_requires_timing_recipient_and_scope():
    # A payment order gets the urgent notice and the conversation continues (late fees,
    # gate 1). A complete objection record only marks the deadline as met.
    c=payment()
    d=gate(c,TODAY)
    assert d.route is Route.PROCEED and d.urgent
    assert [r.rule for r in d.reasons]==['P1-sufficient','U1-payment-order']
    assert compute_deadlines(c,TODAY)[0].action_done
    for key in ('objection_date','objection_recipient','objection_scope','service_disputed'):
        c=payment(); c.facts.pop(key)
        assert gate(c,TODAY).urgent
        assert not compute_deadlines(c,TODAY)[0].action_done


@pytest.mark.parametrize('changes', [dict(objection_recipient='creditor'),dict(objection_scope='partial'),
    dict(objection_date=date(2026,11,14)),dict(service_disputed=True),dict(objection_recipient='server')])
def test_problematic_objection_referred_without_validity_finding(changes):
    assert gate(payment(**changes),TODAY).route is Route.REFER


def test_earlier_order_not_hidden_by_later_reminder():
    c=make('debt_collection',{**DEBT,'earlier_official_document':True})
    assert gate(c,TODAY).route is Route.REFER
    assert gate(c,TODAY).urgent


def test_appointed_heir_uses_official_notification():
    c=make('inheritance_debt',{**ESTATE,'heir_basis':'appointed',
        'date_learned_of_death':date(2026,1,1),'appointment_notice_date':date(2026,11,2)})
    assert compute_deadlines(c,TODAY)[0].due == date(2027,2,2)
    assert gate(c,TODAY).route is Route.PROCEED


@pytest.mark.parametrize('changes,route,urgent', [
    (dict(heir_basis='successor',heir_knowledge_date=date(2026,11,3)), Route.PROCEED, False),
    (dict(estate_actions='took'), Route.REFER, False),
    (dict(estate_actions='unsure'), Route.REFER, False),
    (dict(date_learned_of_death=date(2026,6,1),estate_insolvency='none_known'), Route.REFER, True),
    (dict(date_learned_of_death=date(2026,6,1),estate_insolvency='manifest'), Route.PROCEED, False),
    (dict(disclaimer_filed=True), Route.PROCEED, False)])
def test_estate_branches(changes,route,urgent):
    d=gate(make('inheritance_debt',{**ESTATE,**changes}),TODAY)
    assert d.route is route and d.urgent is urgent


def test_public_inventory_month_is_shown_next_to_the_three_months():
    c=make('inheritance_debt',{**ESTATE,'date_learned_of_death':date(2026,10,15),
        'estate_finances':'uncertain'})
    d=gate(c,TODAY)
    assert d.route is Route.PROCEED and not d.urgent
    assert next(x for x in d.deadlines if x.key=='inventory').due == date(2026,11,15)
    assert next(x for x in d.deadlines if x.key=='disclaimer').due == date(2027,1,15)


def test_all_questions_have_bilingual_explanations_and_labels():
    for name,spec in FIELD_BY_NAME.items():
        assert all(spec.question.get(lang) and WHY[name].get(lang) and LABELS[name].get(lang) for lang in ('de','en'))


def test_payment_order_facts_are_recorded_but_never_asked():
    c=make('debt_collection',dict(document_type='payment_order'))
    assert [x.name for x in required_fields(c)]==['document_type','principal_status','default_trigger']
    for name in ('document_received_date','objection_filed','service_disputed','objection_date',
                 'objection_recipient','objection_scope','objection_amount',
                 'earlier_official_document','claim_amount'):
        assert FIELD_BY_NAME[name].ask is False


def test_retracted_known_fact_cannot_remain_safe():
    from handover.extract import apply_extraction
    c=make('debt_collection',DEBT)
    c.messages=[('user','I do not know who sent it after all.')]
    apply_extraction(c,{'facts':{'document_type':{'user_does_not_know':True,'evidence':'I do not know who sent it after all.'}}},TODAY)
    assert gate(c,TODAY).route is Route.REFER


def test_invalid_correction_does_not_preserve_old_value():
    from handover.extract import apply_extraction
    c=make('debt_collection',DEBT)
    c.messages=[('user','The amount is unclear.')]
    apply_extraction(c,{'facts':{'claim_amount':{'value':float('nan'),'evidence':'The amount is unclear.'},
                                 'principal_status':{'value':'somehow','evidence':'The amount is unclear.'}}},TODAY)
    assert c.value('claim_amount') is None and c.value('principal_status') is None
    assert gate(c,TODAY).route is Route.ASK


@pytest.mark.parametrize('doc,route',[('seizure_notice',Route.REFER),('payment_order',Route.PROCEED)])
def test_unknown_official_period_remains_urgent(doc,route):
    c=make('debt_collection',{**DEBT,'document_type':doc})
    c.facts['document_received_date']=Fact('document_received_date',Status.USER_UNKNOWN)
    d=gate(c,TODAY)
    assert d.route is route and d.urgent


def test_court_letter_is_referred_without_the_urgent_mark():
    # Decided by the legal lead on 2026-11-13: in the area of late fees only a letter
    # from the debt enforcement office is marked urgent.
    d=gate(make('debt_collection',dict(document_type='court_document')),TODAY)
    assert d.route is Route.REFER and not d.urgent
    assert [r.rule for r in d.reasons]==['R5-advanced-proceedings']


def test_completed_other_deadline_cannot_mask_unknown_inheritance_period():
    c=payment()
    c.areas['inheritance_debt']='appointed heir'
    for k,v in {**ESTATE,'heir_basis':'appointed'}.items():
        c.facts[k]=Fact(k,Status.KNOWN,v,'user statement')
    c.facts['appointment_notice_date']=Fact('appointment_notice_date',Status.USER_UNKNOWN)
    d=gate(c,TODAY)
    assert d.route is Route.REFER and d.urgent
    assert any(x.action_done for x in d.deadlines)
    assert not any(x.key=='disclaimer' for x in d.deadlines)


def test_reported_disclaimer_briefing_cites_form_and_creditor_liability():
    from handover.answer import load_corpus
    from handover.briefing import relevant_sources
    from handover.issues import ISSUES, ISSUE_BY_ID
    corpus=load_corpus()
    assert all(k in corpus for i in ISSUES for k in i.statutes)
    issue=ISSUE_BY_ID['disclaimer_effect']
    assert 'Art. 579 ZGB' in issue.title['de'] and 'Art. 579 ZGB' in issue.title['en']
    assert 'fünf Jahre' in corpus['zgb-579']['text']
    c=make('inheritance_debt',{**ESTATE,'disclaimer_filed':True})
    cited=[e['citation'] for e in relevant_sources(c,gate(c,TODAY),corpus)]
    assert cited[:2]==['Art. 570 ZGB','Art. 579 ZGB']


@pytest.mark.parametrize('lang',['de','en'])
def test_unknown_deadline_warning_survives_offer_and_decline(lang):
    from handover.engine import Session
    from handover.llm import FakeLLM
    from handover import texts
    s=Session(FakeLLM([]),today=TODAY,language=lang)
    s.case=make('debt_collection',{**DEBT,'document_type':'seizure_notice'})
    s.case.language=lang
    offer=s._decide_and_respond()
    warning=texts.URGENT_REVIEW_WARNING[lang]
    assert warning in offer.text and warning in offer.data['message']
    declined=s.answer_handover(False)
    assert warning in declined.text and warning in declined.data['deadline_notes']
    assert declined.data['urgent'] and not s.closed
