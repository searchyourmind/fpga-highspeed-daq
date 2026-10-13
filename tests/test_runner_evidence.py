import pytest
from tools.check_junit import require_pass

def test_passing_junit(tmp_path):
    p=tmp_path/'result.xml';p.write_text('<testsuites><testsuite><testcase name="works"/></testsuite></testsuites>')
    assert require_pass(p)==1

@pytest.mark.parametrize('body',['<failure/>','<error/>','<skipped/>'])
def test_failures_and_skips_do_not_pass(tmp_path,body):
    p=tmp_path/'result.xml';p.write_text(f'<testsuite><testcase name="bad">{body}</testcase></testsuite>')
    with pytest.raises(RuntimeError):require_pass(p)

def test_empty_junit_does_not_pass(tmp_path):
    p=tmp_path/'result.xml';p.write_text('<testsuite tests="10" failures="0"/>')
    with pytest.raises(RuntimeError):require_pass(p)
