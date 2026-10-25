async page => {
  await page.evaluate(() => sessionStorage.setItem('chat_test_config', JSON.stringify({
    api: 'http://localhost:8080/api', origin: 'http://localhost:8080',
    userA: 'local_browser_20261010_release_a', userB: 'local_browser_20261010_release_b',
  })));
  return 'Local release browser configured';
}
