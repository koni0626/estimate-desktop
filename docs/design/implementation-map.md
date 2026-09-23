# 要件・実装・検証の対応表

|要件|主要ソース|主な確認方法|
|---|---|---|
|FR-01 認証|`backend/app/main.py`, `security.py`, `models.py`|`tests/test_workflows.py`、デモログイン|
|FR-02 会社・組織分離|`backend/app/main.py`, `projects.py`, `commerce.py`, `models.py`|会社間・課間アクセス試験|
|FR-03 取引先|`backend/app/main.py`, `frontend/src/main.tsx`|取引先の登録・編集|
|FR-04 案件・要望|`backend/app/projects.py`, `frontend/src/projects.tsx`|`tests/test_projects.py`|
|FR-05/06 見積と計算|`backend/app/main.py`, `schemas.py`, `frontend/src/api.ts`|`tests/test_workflows.py`、金額確認|
|FR-07 承認|`backend/app/main.py`, `frontend/src/main.tsx`|`tests/test_workflows.py`、staff→manager→director|
|FR-08 PDF|`backend/app/pdf.py`, `main.py`|発行・PDF取得、旧版保持の試験|
|FR-09 印鑑|`backend/app/commerce.py`, `frontend/src/commerce.tsx`|`tests/test_commerce.py`|
|FR-10 改版・履歴|`backend/app/main.py`, `models.py`|`tests/test_workflows.py`|
|FR-11 受注|`backend/app/commerce.py`, `frontend/src/commerce.tsx`|`tests/test_commerce.py`|
|FR-12 請求・入金|`backend/app/commerce.py`, `pdf.py`|`tests/test_commerce.py`|
|FR-13 添付|`backend/app/attachments.py`, `frontend/src/attachments.tsx`|`tests/test_attachments.py`|
|FR-14 初回セットアップ|`backend/app/main.py`, `schemas.py`, `frontend/src/main.tsx`|`tests/test_initial_setup.py`、空DB起動|
|Windowsデスクトップ配布|`desktop.py`, `scripts/build_desktop.ps1`, `scripts/package_desktop.py`|`tests/test_desktop.py`、EXEの空DB・既存DB起動、Origin検査|

これはコードの検索を助ける目次である。正確な検証結果は[検証記録](verification-results.md)を参照する。
