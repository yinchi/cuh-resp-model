(switchOn) => {
    document.documentElement.setAttribute(
        'data-mantine-color-scheme', switchOn ? 'dark' : 'light');  
    return window.dash_clientside.no_update
}