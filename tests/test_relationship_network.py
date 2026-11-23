import relationship_network as rn


def test_network_edges_are_co_mentions_with_provenance():
    articles = [
        {'title': 'إيران والولايات المتحدة في مفاوضات', 'summary': 'إيران والولايات المتحدة تناقشان الملف النووي', 'url': 'https://example.com/a', 'domain': 'example.com'},
        {'title': 'إيران وإسرائيل', 'summary': 'إيران وإسرائيل في تصعيد', 'url': 'https://other.test/b', 'domain': 'other.test'},
    ]
    net = rn.build_network(articles)
    assert net['stats']['article_count'] == 2
    pair = next(e for e in net['edges'] if {e['source'], e['target']} == {'إيران', 'الولايات المتحدة'})
    assert pair['weight'] == 1
    assert pair['relation_type'] == 'co_mentioned'
    assert 'لا يثبت' in pair['caveat']
    assert pair['evidence'][0]['url'] == 'https://example.com/a'


def test_network_deduplicates_same_url_and_supports_threshold():
    articles = [
        {'title': 'إيران والولايات المتحدة', 'url': 'https://example.com/a'},
        {'title': 'إيران والولايات المتحدة', 'url': 'https://example.com/a'},
    ]
    net = rn.build_network(articles)
    pair = next(e for e in net['edges'] if {e['source'], e['target']} == {'إيران', 'الولايات المتحدة'})
    assert pair['weight'] == 1
    assert rn.build_network(articles, min_co_mentions=2)['edges'] == []


def test_dot_and_prompt_keep_caveats():
    net = rn.build_network([{'title': 'إيران والولايات المتحدة', 'url': 'https://example.com/a'}])
    dot = rn.to_dot(net)
    prompt = rn.build_review_prompt('اختبار', net)
    assert 'graph Marsad' in dot
    assert 'لا تحولها إلى علاقات واقعية مثبتة' in prompt
    assert 'ظهورهما معاً' in prompt
