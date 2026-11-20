# 여주시 지속가능발전협의회 홈페이지 (리뉴얼 시안)

기존 PHP(XpressEngine) 홈페이지(yeoju21.or.kr)를 서버 프로그램 없이 동작하는 정적 사이트로 다시 만든 것입니다.
글은 `content/` 폴더의 파일로, 사진과 첨부파일은 `uploads/` 폴더에 저장됩니다.

## 글 쓰는 방법 (담당자용)

1. https://app.pagescms.org 에 접속해 로그인합니다.
   - GitHub 계정이 없는 담당자는 저장소 관리자가 **이메일로 초대**(Pages CMS의 Collaborators)하면 그 이메일로 로그인할 수 있습니다.
2. `yeoju21_re` 저장소를 엽니다. 왼쪽에 게시판 목록(소통공간 · 공지사항 등)이 나옵니다.
3. 게시판을 고르고 **Add an entry**(새 글)를 누른 뒤 제목, 작성일, 본문을 입력하고 **Save**를 누릅니다.
   - 본문에 사진을 넣거나, 첨부파일 칸에 한글·PDF 파일을 올릴 수 있습니다.
   - 사진은 휴대폰 원본 그대로 올려도 됩니다. 저장 후 GitHub가 **긴 변 1600px 이하로 자동으로 줄여** 다시 저장합니다.
4. 저장하고 1~3분 뒤 홈페이지에 반영됩니다. (진행 상황: 저장소의 **Actions** 탭)

## 구조

| 경로 | 내용 |
|---|---|
| `site.yml` | 사이트 이름, 메뉴, 게시판 목록 설정 |
| `content/<게시판>/*.md` | 글 (위쪽 `---` 사이에 제목·날짜·첨부, 그 아래 본문) |
| `uploads/` | 사진·첨부파일 (`migrated/` 는 기존 사이트에서 옮겨 온 파일) |
| `templates/` | 페이지 디자인(HTML) |
| `css/`, `images/` | 스타일과 고정 이미지 |
| `scripts/build.py` | 글 파일로 사이트를 만드는 프로그램 |
| `scripts/resize_images.py` | 큰 사진 자동 축소 |
| `.pages.yml` | 글쓰기 화면(Pages CMS) 설정 |
| `.github/workflows/deploy.yml` | 저장할 때마다 사진 축소 → 사이트 생성 → 배포 |

## 게시판

- 소통공간: 공지사항(notice), 참여게시판(bbs), 지속가능발전소식(news), 환경상식(general), 자료실(pds)
- 갤러리: 사진갤러리(gallery), 영상갤러리(media)
- 분과: 기후생태(city), 먹거리농업(eco), 지속가능발전교육(edu), 지역문화(local), 사회경제(society)

## 처음 설정 (한 번만)

- 저장소 **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 바꿉니다.
- 자체 도메인으로 옮길 때는 `site.yml` 의 `baseurl` 을 `""` 로, `draft` 를 `false` 로 바꿉니다.

## 직접 만들어 보기

```bash
pip install pillow pyyaml jinja2 markdown
python scripts/build.py      # 결과는 _site/ 폴더
```
