def html(targets):
    basehtml = '<div class="select-box"><p class="text-center sub-sub-header">{name}</p><div class="text-center"><a href="/gcode/{name}" class="hover:underline hover:font-bold">download </a><a href="/print/{name}" class="hover:underline hover:font-bold">print </a><a href="/delete/{name}" class="hover:underline hover:font-bold">delete</a></div></div>'
    if type(targets) == str:
        return basehtml.replace('{name}', targets)
    else:
        output = ''
        for i in range(len(targets)):
            output = output + basehtml.replace('{name}', targets[i])
        return output