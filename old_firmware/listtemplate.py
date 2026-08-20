from pathlib import Path
def html(targets):
    basehtml = '<div class="select-box"><p class="text-center sub-sub-header">{name}</p><div class="text-center"><a href="/gcode/{name}" class="hover:underline hover:font-bold">download </a><a href="/print/{name}" class="hover:underline hover:font-bold">{print} </a><a href="/delete/{name}" class="hover:underline hover:font-bold">delete</a></div></div>'
    if type(targets) == str:
        if '.' in targets[i]:
            if Path('gcode/'+targets).suffix.lower() == '.py':
                print = 'run'
            else:
                print = 'print'
            return basehtml.replace('{name}', targets).replace('{print}', print)
        return 
    else:
        output = ''
        for i in range(len(targets)):
            if '.' in targets[i]:
                if Path(targets[i]).suffix.lower() == '.py':
                    print = 'run'
                else:
                    print = 'print'
                output = output + basehtml.replace('{name}', targets[i]).replace('{print}', print)
        return output