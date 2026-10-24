@echo off
chcp 65001 > nul
echo =====================================================================
echo   Google Drive Git 저장소 로컬 분리 자동 설정 스크립트 (setup_local)
echo =====================================================================
echo.
echo [1/5] 로컬 작업 디렉토리(C:\workspace)를 확인 및 생성합니다...
if not exist "C:\workspace" (
    mkdir "C:\workspace"
    echo   - C:\workspace 생성 완료.
) else (
    echo   - C:\workspace 가 이미 존재합니다.
)
echo.

echo [2/5] GitHub에서 acupoint_anatomy 를 로컬로 클론합니다...
if not exist "C:\workspace\acupoint_anatomy\.git" (
    git clone https://jaehyokim-sketch@github.com/jaehyokim-sketch/acupoint_anatomy.git "C:\workspace\acupoint_anatomy"
) else (
    echo   - C:\workspace\acupoint_anatomy 가 이미 존재합니다. 최신 버전을 가져옵니다...
    git -C "C:\workspace\acupoint_anatomy" pull origin main
)
echo.

echo [3/5] GitHub에서 huanglongxiang-scholar 를 로컬로 클론합니다...
if not exist "C:\workspace\huanglongxiang-scholar\.git" (
    git clone https://jaehyokim-sketch@github.com/jaehyokim-sketch/huanglongxiang-scholar.git "C:\workspace\huanglongxiang-scholar"
) else (
    echo   - C:\workspace\huanglongxiang-scholar 가 이미 존재합니다. 최신 버전을 가져옵니다...
    git -C "C:\workspace\huanglongxiang-scholar" pull origin main
)
echo.

echo [4/5] 로컬 저장소 Git 사용자 정보(jaehyokim)를 설정합니다...
git -C "C:\workspace\acupoint_anatomy" config user.name "jaehyokim"
git -C "C:\workspace\acupoint_anatomy" config user.email "jaehyo.kim@gmail.com"
git -C "C:\workspace\acupoint_anatomy" config credential.helper manager

git -C "C:\workspace\huanglongxiang-scholar" config user.name "jaehyokim"
git -C "C:\workspace\huanglongxiang-scholar" config user.email "jaehyo.kim@gmail.com"
git -C "C:\workspace\huanglongxiang-scholar" config credential.helper manager
echo   - 사용자 설정 완료.
echo.

echo [5/5] 구글 드라이브 내 충돌 유발 .git 폴더를 안전하게 제거합니다...
if exist "%~dp0acupoint_anatomy\.git" (
    rd /s /q "%~dp0acupoint_anatomy\.git" 2>nul
    echo   - acupoint_anatomy\.git 제거 완료.
)
if exist "%~dp001_황룡상 스킬\.git" (
    rd /s /q "%~dp001_황룡상 스킬\.git" 2>nul
    echo   - 01_황룡상 스킬\.git 제거 완료.
)
echo.
echo =====================================================================
echo   모든 로컬 분리 설정이 성공적으로 완료되었습니다!
echo   - 개발 작업 위치 : C:\workspace\acupoint_anatomy
echo                     C:\workspace\huanglongxiang-scholar
echo   - 드라이브 배포 : 각 폴더의 deploy_to_gdrive.bat 실행
echo =====================================================================
echo.
pause
