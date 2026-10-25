async host => {
  const ctx=await host.context().browser().newContext({serviceWorkers:'allow'});
  const page=await ctx.newPage();
  try {
    await page.goto('http://localhost:8089/app');
    await page.getByText('Не удалось сохранить файлы приложения.',{exact:false}).waitFor();
    await page.getByText('Файлы приложения не сохранены.',{exact:false}).waitFor();
    await page.getByRole('button',{name:'Перезагрузить и повторить',exact:true}).waitFor();
    const failed=await page.evaluate(()=>!navigator.serviceWorker.controller);
    await Promise.all([page.waitForEvent('load'),page.getByRole('button',{name:'Перезагрузить и повторить',exact:true}).click()]);
    await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
    await page.getByText('Файлы приложения сохранены.',{exact:false}).waitFor();
    if(await page.locator('.app-error').count())throw Error('Recovered app retained an error');
    await ctx.setOffline(true);await page.goto('http://localhost:8089/app?recovered-offline=1');
    await page.getByRole('heading',{name:'Приложение AniLux',exact:true}).waitFor();
    await page.locator('.offline-banner').waitFor();
    return {passed:true,realWorkerInstallFailure:failed,reloadRecovered:true,offlineAfterRecovery:true};
  } finally {await ctx.setOffline(false);await ctx.close();}
}
