async host => {
  const context=await host.context().browser().browserType().launchPersistentContext('C:/Users/Serezhka/Documents/Projects/Kaiden/Web/Production/animecore/backend/data/local_release/ui-review/pwa-device-profile',{
    channel:'chrome',headless:true,ignoreDefaultArgs:['--disable-background-networking'],viewport:{width:390,height:844},permissions:['notifications'],
  });
  try {
    const page=await context.newPage();await page.goto('http://localhost:5187/app');
    await page.getByRole('button',{name:'Выключить на этом устройстве',exact:true}).click();
    await page.getByRole('button',{name:'Включить уведомления',exact:true}).waitFor();
    const removed=await page.evaluate(async()=>!await (await navigator.serviceWorker.getRegistration()).pushManager.getSubscription());
    if(!removed)throw Error('Subscription not removed');return {passed:true,subscriptionRemoved:removed};
  } finally {await context.close();}
}
