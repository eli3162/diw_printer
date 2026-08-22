def html(targets):
    basehtml = '<div class="select-box"><p class="text-center sub-sub-header">{name}</p><div class="text-center"><a href="/{name}">download </a><a href="/print/{name}">{print} </a><a href="/delete/{name}">delete</a></div></div>'
    if type(targets) == str:
        if '.' in targets:
            if '.py' in targets:
                printname = 'run'
            else:
                printname = 'print'
            return basehtml.replace('{name}', targets).replace('{print}', printname)
        return 
    else:
        output = ''
        for i in range(len(targets)):
            if '.' in targets[i]:
                if '.py' in targets[i]:
                    printname = 'run'
                else:
                    printname = 'print'
                output = output + basehtml.replace('{name}', targets[i]).replace('{print}', printname)
        return output