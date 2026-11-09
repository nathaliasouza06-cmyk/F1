function setState(s){document.body.dataset.state=s;document.getElementById('state').textContent=s}
function account(s){document.body.dataset.account=s;document.getElementById('account').textContent=s}
if(document.cookie.includes('sim_login=yes'))account('Conta conectada');
document.getElementById('login').onclick=()=>{document.cookie='sim_login=yes; SameSite=Strict; Max-Age=86400; Path=/sim';account('Conta conectada')};
document.getElementById('expire').onclick=()=>{document.cookie='sim_login=; Max-Age=0; Path=/sim';account('Sessão expirada');setState('Sessão expirada')};
for(const [id,s] of Object.entries({human:'CAPTCHA ou verificação humana',waiting:'Sala de espera disponível',enter:'Sala de espera acessada',queue:'Fila virtual ativa',turn:'Aguardando sua vez',select:'Escolha de ingressos liberada'}))document.getElementById(id).onclick=()=>setState(s);
document.getElementById('sequence').onclick=()=>{setState('Venda ainda não iniciada');setTimeout(()=>setState('Sala de espera disponível'),15000);setTimeout(()=>setState('Fila virtual ativa'),45000);setTimeout(()=>setState('Escolha de ingressos liberada'),75000)};
