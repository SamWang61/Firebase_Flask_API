"use strict";
const $=id=>document.getElementById(id);
$("temperature").addEventListener("input",()=>{$("value").value=Number($("temperature").value).toFixed(1);});
$("form").addEventListener("submit",async event=>{
  event.preventDefault();$("submit").disabled=true;$("status").textContent="查詢天氣與 AI 分析中…";$("answer").textContent="請稍候。";$("debug").textContent="";
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
  try{
    const response=await fetch("/api/weather",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({city:$("city").value,question:$("question").value,temperature:Number($("temperature").value)}),signal:controller.signal});
    const body=await response.json();$("debug").textContent=JSON.stringify({weather:body.data?.weather,debug:body.debug},null,2);
    if(!response.ok||!body.ok)throw new Error(body.error||`HTTP ${response.status}`);
    $("answer").textContent=body.data.answer;$("status").textContent=`完成｜${body.data.weather.location}｜Temperature ${body.data.temperature}`;
  }catch(error){$("answer").textContent=error.name==="AbortError"?"瀏覽器等待超過 45 秒，請稍後再試。":error.message;$("status").textContent="查詢失敗";}
  finally{clearTimeout(timer);$("submit").disabled=false;}
});
