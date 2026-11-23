import pytest
import article_script_prompts as mod


def test_single_article_prompt_keeps_provenance_and_safety_rules():
    prompt = mod.build_script_prompt([{
        'title_ar': 'عنوان عربي', 'title_en': 'English headline',
        'outlet': 'Ynet', 'writer': 'Analyst', 'url': 'https://example.com/a',
        'snip_ar': 'مقتطف متاح فقط'
    }])
    assert 'https://example.com/a' in prompt
    assert 'Ynet' in prompt
    assert 'لا تفترض أن النص كامل' in prompt
    assert 'فنّد كل ادعاء مهم' in prompt
    assert 'سكريبت' in prompt
    assert 'لا تحاول تجاوز الاشتراك' in prompt


def test_multi_article_prompt_includes_each_source():
    prompt = mod.build_script_prompt([
        {'title': 'A', 'url': 'https://a.example'},
        {'title': 'B', 'url': 'https://b.example'},
    ])
    assert '[1]' in prompt and '[2]' in prompt
    assert 'https://a.example' in prompt and 'https://b.example' in prompt


def test_empty_prompt_input_rejected():
    with pytest.raises(ValueError):
        mod.build_script_prompt([])


def test_alternative_search_links_use_title_and_author():
    links = mod.alternative_search_links({'title_en': 'Paid headline', 'title_ar': 'عنوان', 'writer': 'Writer'})
    assert links
    assert any('Paid+headline' in x['google'] or 'Paid%2Bheadline' in x['google'] for x in links)
    assert all(x['google'].startswith('https://www.google.com/search?q=') for x in links)
    assert all(x['news'].startswith('https://news.google.com/search?q=') for x in links)
