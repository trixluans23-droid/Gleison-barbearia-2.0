from pathlib import Path

p = Path("site/index.html")
s = p.read_text(encoding="utf-8")

code = r'''
<style id="foto-perfil-cliente-style">
.gc-foto-perfil-wrap{display:flex;flex-direction:column;align-items:center;gap:10px;margin:4px 0 14px}
.gc-foto-perfil-preview{width:108px;height:108px;border-radius:50%;object-fit:cover;border:3px solid #f2c14e;background:#171c20;display:block}
.gc-foto-perfil-placeholder{display:flex;align-items:center;justify-content:center;font-size:48px;color:#8f989f}
.gc-foto-perfil-input{width:100%;font-size:14px!important;padding:10px!important}
.gc-foto-perfil-btn{width:100%;background:#f2c14e!important;color:#171717!important}
</style>
<script id="foto-perfil-cliente-script">
(function(){
  var PHONE_KEY="gleison_telefone";
  function sb(){try{return window.supabaseClient||supabaseClient||null}catch(e){return window.supabaseClient||null}}
  function digits(v){return String(v||"").replace(/\D/g,"")}
  function msg(t,c){var e=document.getElementById("gc-perfil-msg");if(e){e.textContent=t||"";e.className=c||"gc-info"}}
  function telefone(){return localStorage.getItem(PHONE_KEY)||""}
  function preview(url){
    var e=document.getElementById("gc-foto-perfil-preview"); if(!e)return;
    if(url){
      e.style.display="block";
      e.alt="";
      e.onerror=function(){
        e.onerror=null;
        e.removeAttribute("src");
        e.alt="";
        e.style.display="block";
        e.style.background="#171c20";
      };
      e.src=url;
    }else{
      e.removeAttribute("src");
      e.alt="";
      e.style.display="block";
      e.style.background="#171c20";
    }
  }
  async function carregar(){
    var tel=telefone(),client=sb(); if(digits(tel).length!==11||!client){preview("");return}
    try{
      var r=await client.rpc("obter_foto_cliente",{p_telefone:tel});
      if(r.error)throw r.error;
      var row=Array.isArray(r.data)?(r.data[0]||null):r.data;
      var foto=row&&row.foto_url?String(row.foto_url):"";
      if(foto && !/^https?:|^data:/i.test(foto)){
        var pu=client.storage.from("fotos-clientes").getPublicUrl(foto);
        foto=pu&&pu.data&&pu.data.publicUrl?pu.data.publicUrl:"";
      }
      preview(foto ? foto + (foto.indexOf("?")>=0?"&":"?")+"v="+Date.now() : "");
    }catch(e){console.warn("Foto do perfil:",e);preview("")}
  }
  function comprimir(file){
    return new Promise(function(resolve,reject){
      var reader=new FileReader();
      reader.onload=function(){var img=new Image();img.onload=function(){
        var max=700,scale=Math.min(1,max/Math.max(img.width,img.height)),w=Math.max(1,Math.round(img.width*scale)),h=Math.max(1,Math.round(img.height*scale));
        var c=document.createElement("canvas");c.width=w;c.height=h;c.getContext("2d").drawImage(img,0,0,w,h);
        var q=.82,data=c.toDataURL("image/jpeg",q);while(data.length>700000&&q>.45){q-=.07;data=c.toDataURL("image/jpeg",q)}resolve(data);
      };img.onerror=reject;img.src=reader.result};reader.onerror=reject;reader.readAsDataURL(file)
    })
  }
  async function salvar(){
    var input=document.getElementById("gc-foto-perfil-input"),btn=document.getElementById("gc-foto-perfil-salvar"),file=input&&input.files&&input.files[0],tel=telefone(),client=sb();
    if(!file){msg("Escolha uma foto primeiro.","gc-erro");return}
    if(digits(tel).length!==11){msg("Seu telefone não está cadastrado corretamente.","gc-erro");return}
    if(!/^image\//i.test(file.type)){msg("Escolha uma imagem.","gc-erro");return}
    if(file.size>8*1024*1024){msg("A foto é muito grande. Escolha uma imagem menor.","gc-erro");return}
    if(!client){msg("Sistema ainda está carregando. Tente novamente.","gc-erro");return}
    btn.disabled=true;msg("Salvando sua foto...","gc-info");
    try{
      msg("Enviando foto...","gc-info");
      var ext=(file.name.split(".").pop()||"jpg").toLowerCase().replace(/[^a-z0-9]/g,"")||"jpg";
      var path=digits(tel)+"/perfil."+ext;
      var up=await client.storage.from("fotos-clientes").upload(path,file,{contentType:file.type,upsert:true});
      if(up.error)throw up.error;
      var r=await client.rpc("salvar_foto_cliente",{p_telefone:tel,p_foto_url:path});
      if(r.error)throw r.error;
      if(r.data!==true)throw new Error("Cliente não encontrado.");
      var pu=client.storage.from("fotos-clientes").getPublicUrl(path);
      var url=pu&&pu.data&&pu.data.publicUrl?pu.data.publicUrl:"";
      preview(url ? url+(url.indexOf("?")>=0?"&":"?")+"v="+Date.now() : "");
      input.value="";
      msg("Foto atualizada com sucesso!","gc-ok");
    }
    catch(e){console.error("Salvar foto:",e);msg(e.message||"Não foi possível salvar a foto.","gc-erro")}finally{btn.disabled=false}
  }
  function preparar(){
    var modal=document.getElementById("gc-perfil-overlay");if(!modal||document.getElementById("gc-foto-perfil-input"))return;
    var wrap=document.createElement("div");wrap.className="gc-foto-perfil-wrap";
    wrap.innerHTML='<img id="gc-foto-perfil-preview" class="gc-foto-perfil-preview gc-foto-perfil-placeholder" alt="Sem foto" src="" />'+
      '<label style="width:100%;margin:0">Foto do perfil</label>'+
      '<input id="gc-foto-perfil-input" class="gc-foto-perfil-input" type="file" accept="image/*" style="display:none">'+
      '<button type="button" id="gc-foto-perfil-salvar" class="gc-foto-perfil-btn">📷 Adicionar / alterar foto</button>';
    var p=modal.querySelector("p");if(p)p.insertAdjacentElement("afterend",wrap);
    document.getElementById("gc-foto-perfil-salvar").addEventListener("click",function(){document.getElementById("gc-foto-perfil-input").click()});
    document.getElementById("gc-foto-perfil-input").addEventListener("change",function(){var f=this.files&&this.files[0];if(f){preview(URL.createObjectURL(f));salvar()}});
    carregar()
  }
  function abrirNoNavegador(){
    var tel=telefone(),base=location.origin+location.pathname;
    var alvo=base+"?foto_perfil=1&telefone="+encodeURIComponent(tel);
    var box=document.getElementById("gc-foto-perfil-link-box");
    var link=document.getElementById("gc-foto-perfil-link");
    if(box&&link){
      link.href=alvo; link.textContent=alvo;
      box.style.display="block";
      msg("Abra este link no Chrome para escolher sua foto.","gc-info");
      try{
        if(navigator.clipboard&&navigator.clipboard.writeText){
          navigator.clipboard.writeText(alvo).then(function(){msg("Link copiado. Abra o Chrome e cole o link.","gc-ok")}).catch(function(){});
        }
      }catch(e){}
    }
  }
  function prepararBotaoNavegador(){
    var b=document.getElementById("gc-foto-perfil-navegador");
    if(b&&!b.__ligado){b.__ligado=true;b.addEventListener("click",abrirNoNavegador)}
  }
  function abrirPerfilAutomaticamente(){
    try{
      var q=new URLSearchParams(location.search);
      var tel=q.get("telefone");
      if(q.get("foto_perfil")==="1"&&digits(tel).length===11){
        localStorage.setItem(PHONE_KEY,tel);
        setTimeout(function(){
          var pm=document.querySelector('[data-menu-acao="perfil"]');
          if(pm)pm.click();
        },1200);
      }
    }catch(e){}
  }
  function iniciar(){
    abrirPerfilAutomaticamente();
    preparar();
    var pm=document.querySelector('[data-menu-acao="perfil"]');
    if(pm)pm.addEventListener("click",function(){setTimeout(function(){preparar();carregar()},120)},true);
    var obs=new MutationObserver(function(){preparar()});
    if(document.body)obs.observe(document.body,{childList:true,subtree:true})
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",function(){setTimeout(iniciar,700)});else setTimeout(iniciar,700)
})();
</script>
'''
if 'id="foto-perfil-cliente-script"' not in s and "</body>" in s:
    s = s.replace("</body>", code + "</body>", 1)
p.write_text(s, encoding="utf-8")
print("Opção de alteração da foto do cliente adicionada ao Perfil.")
