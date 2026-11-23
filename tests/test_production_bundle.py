import io
import json
import zipfile
import pytest

import production_bundle


def test_build_production_bundle_contains_expected_files():
    job = {
        "id": "content_123", "case_id": "case_1", "case_title": "اختبار القضية",
        "result_id": "result_1", "output_type": "حزمة كاملة", "platform": "يوتيوب",
        "dialect": "عامية مصرية مبسطة", "duration": "3 دقائق",
    }
    result = {
        "text": "# Storyboard\nمشهد أول\n\n# البرومبتات البصرية\nلقطة توضيحية",
        "provider": "groq", "model": "test-model",
    }
    data = production_bundle.build_production_bundle(job, result)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        prefix = "content_123/"
        expected = {
            "README.md", "01_content_full.md", "02_storyboard.md",
            "03_visual_prompts.md", "04_asset_manifest.csv",
            "05_edit_decision_list.tsv", "06_production_job.json",
            "07_quality_checklist.md", "09_generated_images_manifest.json",
        }
        assert {n[len(prefix):] for n in names} == expected
        metadata = json.loads(archive.read(prefix + "06_production_job.json"))
        assert metadata["result"]["media_assets_included"] is False
        assert "Storyboard" in archive.read(prefix + "02_storyboard.md").decode("utf-8")
        assert "track\tstart" in archive.read(prefix + "05_edit_decision_list.tsv").decode("utf-8")


def test_bundle_requires_generated_content():
    with pytest.raises(ValueError):
        production_bundle.build_production_bundle({"id": "job"}, {"text": "  "})


def test_safe_job_name():
    assert production_bundle._clean_name("عربي / !!") == "marsad_production"


def test_bundle_includes_generated_scene_images():
    job = {"id": "content_456", "case_title": "مشهد اختبار"}
    result = {"text": "# محتوى\nنص", "provider": "groq", "model": "test"}
    image = {"scene_id": "SH001", "version": 1, "filename": "SH001_v01.png",
             "prompt": "cinematic scene", "model": "gpt-image-2", "image_bytes": b"fake-png"}
    data = production_bundle.build_production_bundle(job, result, [image])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.read("content_456/08_generated_images/SH001_v01.png") == b"fake-png"
        manifest = json.loads(archive.read("content_456/09_generated_images_manifest.json"))
        assert manifest[0]["scene_id"] == "SH001"
        assert "image_bytes" not in manifest[0]
        metadata = json.loads(archive.read("content_456/06_production_job.json"))
        assert metadata["result"]["generated_image_count"] == 1
