# 프로그램 명: account_manager
# 설명:
	- local pc에  인터넷의 웹사이트의 수 많은 가입 정보를 저장하고 있는 파일(마크다운 형삭) 또는 sqllite와 같은 데이터베이스애 저장하고 ollama가 제공하는 ai private모델을 이용해서 쉽게 조회하고 업데이트 할 수 있는 프로그램

# 요구사항
 - 인터넷 가입 정보를 손쉽게 편집 할 수 있어야 한다. 나는 그래서 makrdown형삭의 파일이 적합하지 않읅까 생각. LLM을 이용하지 않고 일반 편집기로도 손쉽게 추가 삭제가 가능하는 것이 좋을 것 같음
 - UI/UX은 터미널 기반 챗봇 형태가 좋을 것 같음
 - chatbot은 슬래쉬(/) 명령어를 도입. 예를 들어 /help명령어를 입력하면 간단한 사용법을 보여주고ㅠ /list하면 파일 목록을 보여 주는 것 같은 기능
 - MEMORY.md 파일을 도입해서 매번 새롭개 chatbot을 실행해도 과거의 중요한 내용을 저장
 - HISTORY.md 파일에는 로그인 정보 변경 아력을 기록
  


 # 기술 스팩
  - python을 이용하고 uv로 패키지 관리
  - lnagchain을 기본으로 하고 agent를 구현해야 하는 경우애느 langgraph를 이용
  - ollama애 사용할 모델은 .env파일에서 설정 할 수 있도록 구성
  - local pc에서 사용하자만 적당한 보안 장치 구현
  - embeding이 필요한경우 ollama애서 사용 가능한 embeddinggemma:latest를 사용하세요
  - self correction agent,the reflection agent pattern 등을 사용해서 답변의 정확도를 높이세요
  - 여기에 언급된 내용 이외에 더 좋응 아이디어가 있으면 제안하세요


  # 사용 예시
  '''
  jeahyungchung@JeaHyungui-MacBookPro-684 ~ %account_mng 실생

  > atozjames@gmail.com 패스워드 알려줘?

  > google 계졍 목록 보여워?

  > siteground 로그인 정보 알려줘

  > clickpresso 로그인 정보 저정해줘. 아이디:bomsan69, 비빌번회:12345

  > clickpresso 비말번호를 34567로 변경하고 변경정보를 histoty로 남겨줘

  > 이메일 api 서비스 업체 관련 리스트 보여줘

  '''' 

  # coding guide
  - 코딩을 하기 전에 계획을 수립하고 계획을 수립하는 과정에서 고객의 의도가 명확하게 이해 되지 않을 때는 고객에 질문을 해서 불확실한 내용을 명확히 하세요
  - 계획이 수립되면 PLAN.md파일을 만들고 계획에 따라 작업을 수행하세요
  - 코딩이 완료되면 TEST.md파일을 만들고 테스트 계획을 수립한 후에 테스트를 진행하세요
  - 코딩이 완료되면 README.md 파일을 만들고 배포 방법과 간단한 사용법을 작성하세요