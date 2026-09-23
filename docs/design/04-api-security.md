# 4. API・セキュリティ設計

Windowsデスクトップ版のログイン不要な起動は[7. デスクトップ版の設計](07-desktop-design.md)を優先する。利用者のパスワード入力を省く一方、起動ごとの秘密値、HttpOnly起動Cookie、業務用セッションCookie、Origin検査を使う。以下の通常ログインAPIはブラウザー開発版・複数ユーザーDB用に残す。

## 4.1 APIの入口

APIのベースは `/api`、開発時の仕様確認は `http://127.0.0.1:8005/docs`。業務APIは原則ログイン必須。JSONの入力はPydanticモデルで型・長さ・列挙値を検証し、想定外の項目を拒否する。正常な作成は201、未認証は401、権限なしは403、他社・見えない対象は404、状態や更新競合は409、入力不正は422を基本とする。

|領域|代表的なAPI|実装|
|---|---|---|
|認証・初期表示|`GET /setup/status`, `POST /setup`, `POST /auth/login`, `POST /auth/logout`, `GET /bootstrap`|`backend/app/main.py`|
|取引先|`GET/POST /customers`, `PUT /customers/{id}`|`backend/app/main.py`|
|見積|`GET/POST /quotes`, `GET/PUT /revisions/{id}`, `POST /revisions/{id}/{action}`, `GET /revisions/{id}/pdf`|`backend/app/main.py`|
|承認待ち|`GET /approvals`|`backend/app/main.py`|
|会社管理|`PUT /settings`, `POST /members`, `POST /organizations`, `GET /audit`|`backend/app/main.py`|
|会社印・営業状況|`POST /seals`, `DELETE /seals/current`, `PUT /quotes/{id}/sales`|`backend/app/commerce.py`|
|受注・請求|`GET/POST /orders`, `GET/PUT /orders/{id}`, `POST /orders/{id}/invoices`, `GET/PUT /invoices/{id}`, `POST /invoices/{id}/payment`, `GET /invoices/{id}/pdf`|`backend/app/commerce.py`|
|案件・要望|`GET/POST /projects`, `GET/PUT /projects/{id}`, `POST /projects/{id}/requests`, `POST /projects/{id}/requests/{id}/agree`|`backend/app/projects.py`|
|案件添付|`GET /projects/{id}/attachments`, `PUT /projects/{id}/attachments/{upload_id}`, `GET /projects/{id}/attachments/{id}/download`, `DELETE /projects/{id}/attachments/{id}`|`backend/app/attachments.py`|
|操作マニュアル|`GET /manual/...`|`backend/app/manual.py`|

発行、申請、承認、差戻し、取下げ、改版、複製などは `action` に個別の許可値を渡す。実際に許される操作はサーバー側の現在状態で決まる。画面のボタン非表示は補助にすぎない。完全なリクエスト・レスポンス定義は、起動後のOpenAPI画面と `backend/app/schemas.py` を正本とする。

## 4.2 ログインとセッション

パスワードはソルト付きPBKDF2-SHA256で保存し、照合には定時間比較を使う。成功時にランダムなセッショントークンを発行し、DBにはハッシュのみ保存する。Cookie `estimate2_session` は HttpOnly / SameSite=Lax、12時間の有効期限。`COOKIE_SECURE=true` を指定したHTTPS環境ではSecure属性を付ける。ログアウトでDBのセッションを削除する。無効化された会社・所属は、セッションが残っていても使えない。

初回セットアップの状態照会と登録だけは未認証で受け付ける。登録は事業者・ユーザー・所属がすべて0件の場合に限り、SQLiteの `BEGIN IMMEDIATE` で判定と作成を一つのトランザクションにまとめる。同時登録では一方だけが成功する。管理者パスワードは12文字以上、登録後は通常のセッションを発行する。既存データがあるDBでは再登録を409で拒否する。この例外はローカル初回設定専用であり、継続的な公開サインアップ機能ではない。

現サンプルにはSSO、パスワード再設定、ログイン試行回数制限はない。デモ共通パスワードとダミー取引先を含むため、そのまま外部公開しない。

## 4.3 会社と組織の分離

認証済みの所属から `company_id` を決定し、クライアントから送られた会社IDを信頼しない。単体取得・更新では対象の `company_id` を必ず照合する。見積と案件は役割に応じて課／部／自社の範囲を確認する。現在の承認段階を担当する人には、その見積版に限定した参照を許す。PDFと添付のダウンロードも同じ認可を通す。主なDBリレーションには会社IDを含む複合外部キーを設定する。

## 4.4 ブラウザーからの不正操作への対処

状態変更系のリクエストで `Origin` を確認し、許可する開発用オリジン以外を拒否する。`Sec-Fetch-Site: cross-site` も拒否する。APIレスポンスには `Cache-Control: no-store`、全レスポンスには `X-Content-Type-Options: nosniff` を付ける。添付は拡張子に依存せず受信サイズを検査し、ダウンロードは認証されたAPIから行う。

このOrigin設定はローカル開発用の固定値である。別ホストへ配置する場合は許可オリジン、TLS、Cookie設定、プロキシ、レート制限、バックアップを再設計する。画面のJavaScriptで権限を判断しても、APIの認可は省略しない。
