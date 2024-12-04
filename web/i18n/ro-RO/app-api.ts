const translation = {
  apiServer: 'Server API',
  apiKey: 'Cheia API',
  status: 'Stare',
  disabled: 'Dezactivat',
  ok: 'În Serviciu',
  copy: 'Copiază',
  copied: 'Copiat',
  play: 'Redă',
  pause: 'Pauză',
  playing: 'În redare',
  loading: 'Se încarcă',
  merMaid: {
    rerender: 'Reprocesare',
  },
  never: 'Niciodată',
  apiKeyModal: {
    apiSecretKey: 'Cheia secretă API',
    apiSecretKeyTips: 'Pentru a preveni abuzul API, protejați-vă Cheia API. Evitați utilizarea ei ca text simplu în codul front-end. :)',
    createNewSecretKey: 'Creează o nouă cheie secretă',
    secretKey: 'Cheie Secretă',
    created: 'CREATĂ',
    lastUsed: 'ULTIMA UTILIZARE',
    generateTips: 'Păstrați această cheie într-un loc sigur și accesibil.',
  },
  actionMsg: {
    deleteConfirmTitle: 'Ștergeți această cheie secretă?',
    deleteConfirmTips: 'Această acțiune nu poate fi anulată.',
    ok: 'OK',
  },
  completionMode: {
    title: 'API completare aplicație',
    info: 'Pentru generarea de text de înaltă calitate, cum ar fi articole, rezumate și traduceri, utilizați API-ul de mesaje de completare cu intrare de la utilizator. Generarea de text se bazează pe parametrii modelului și șabloanele de prompturi stabilite în Ingineria Prompturilor Dify.',
    createCompletionApi: 'Creează mesaj de completare',
    createCompletionApiTip: 'Creează un mesaj de completare pentru a sprijini modul de întrebare și răspuns.',
    inputsTips: '(Opțional) Furnizați câmpuri de intrare pentru utilizator ca perechi cheie-valoare, corespunzătoare variabilelor din Ingineria Prompt. Cheia este numele variabilei, Valoarea este valoarea parametrului. Dacă tipul de câmp este Select, Valoarea trimisă trebuie să fie una dintre opțiunile prestabilite.',
    queryTips: 'Conținutul textului de intrare al utilizatorului.',
    blocking: 'Tip blocant, așteptând finalizarea execuției și returnarea rezultatelor. (Cererea poate fi întreruptă dacă procesul este lung)',
    streaming: 'returnare în flux. Implementarea returnării în flux bazată pe SSE (Evenimente trimise de server).',
    messageFeedbackApi: 'Feedback mesaj (apreciere)',
    messageFeedbackApiTip: 'Evaluează mesajele primite în numele utilizatorilor finali cu aprecieri sau dezaprecieri. Aceste date sunt vizibile în pagina Jurnale & Anotații și sunt utilizate pentru ajustarea fină a modelului viitor.',
    messageIDTip: 'ID mesaj',
    ratingTip: 'apreciere sau dezapreciere, nul este anulare',
    parametersApi: 'Obțineți informații despre parametrii aplicației',
    parametersApiTip: 'Recuperați parametrii de intrare configurați, inclusiv numele variabilelor, denumirile câmpurilor, tipurile și valorile implicite. De obicei, sunt folosiți pentru a afișa aceste câmpuri într-un formular sau pentru a completa valorile implicite după încărcarea clientului.',
  },
  chatMode: {
    title: 'API chat aplicație',
    info: 'Pentru aplicații conversaționale versatile folosind un format Q&A, apelați API-ul de mesaje de chat pentru a iniția un dialog. Mențineți conversațiile continue transmitând conversation_id returnat. Parametrii de răspuns și șabloanele depind de setările Ingineriei Prompt Dify.',
    createChatApi: 'Creează mesaj de chat',
    createChatApiTip: 'Creează un nou mesaj de conversație sau continuă un dialog existent.',
    inputsTips: '(Opțional) Furnizați câmpuri de intrare pentru utilizator ca perechi cheie-valoare, corespunzătoare variabilelor din Ingineria Prompt. Cheia este numele variabilei, Valoarea este valoarea parametrului. Dacă tipul de câmp este Select, Valoarea trimisă trebuie să fie una dintre opțiunile prestabilite.',
    queryTips: 'Conținutul întrebării/utilizatorului introdus',
    blocking: 'Tip blocant, așteptând finalizarea execuției și returnarea rezultatelor. (Cererea poate fi întreruptă dacă procesul este lung)',
    streaming: 'returnare în flux. Implementarea returnării în flux bazată pe SSE (Evenimente trimise de server).',
    conversationIdTip: '(Opțional) ID conversație: lăsați gol pentru prima conversație; transmiteți conversation_id din context pentru a continua dialogul.',
    messageFeedbackApi: 'Feedback terminal utilizator mesaj, apreciere',
    messageFeedbackApiTip: 'Evaluează mesajele primite în numele utilizatorilor finali cu aprecieri sau dezaprecieri. Aceste date sunt vizibile în pagina Jurnale & Anotații și sunt utilizate pentru ajustarea fină a modelului viitor.',
    messageIDTip: 'ID mesaj',
    ratingTip: 'apreciere sau dezapreciere, nul este anulare',
    chatMsgHistoryApi: 'Obțineți istoricul mesajelor de chat',
    chatMsgHistoryApiTip: 'Prima pagină returnează ultimele `limită` bare, care sunt în ordine inversă.',
    chatMsgHistoryConversationIdTip: 'ID conversație',
    chatMsgHistoryFirstId: 'ID-ul primului înregistrare de chat de pe pagina curentă. Implicit este niciunul.',
    chatMsgHistoryLimit: 'Câte chat-uri sunt returnate într-o singură cerere',
    conversationsListApi: 'Obțineți lista de conversații',
    conversationsListApiTip: 'Obține lista de sesiuni a utilizatorului curent. În mod implicit, ultimele 20 de sesiuni sunt returnate.',
    conversationsListFirstIdTip: 'ID-ul ultimei înregistrări de pe pagina curentă, implicit niciunul.',
    conversationsListLimitTip: 'Câte chat-uri sunt returnate într-o singură cerere',
    conversationRenamingApi: 'Redenumirea conversației',
    conversationRenamingApiTip: 'Redenumiți conversațiile; numele este afișat în interfețele client cu sesiuni multiple.',
    conversationRenamingNameTip: 'Nume nou',
    parametersApi: 'Obțineți informații despre parametrii aplicației',
    parametersApiTip: 'Recuperați parametrii de intrare configurați, inclusiv numele variabilelor, denumirile câmpurilor, tipurile și valorile implicite. De obicei, sunt folosiți pentru a afișa aceste câmpuri într-un formular sau pentru a completa valorile implicite după încărcarea clientului.',
  },
  develop: {
    requestBody: 'Corpul cererii',
    pathParams: 'Parametrii căii',
    query: 'Interogare',
    toc: 'Conținut',
  },
  regenerate: 'Regenera',
}

export default translation
