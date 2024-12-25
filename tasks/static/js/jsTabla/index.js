document.addEventListener('DOMContentLoaded',()=>{
    const _table = document.getElementById('tbl');
    const _input=document.getElementById('btn_buscar_p');

    _input.addEventListener('input',()=>{
        const words = _input.value;
        const [,...rows] = _table.getElementsByTagName('tr');

        for(const row of rows){
            const [_, nombres, apellidos, dni] = row.children;
            let shouldHide = false;

            if(words){
                shouldHide = !nombres.innerText.includes(words) && !apellidos.innerText.includes(words) && !dni.innerText.includes(words);
            }
            if(shouldHide){
                row.classList.add('d-none');
            }else{
                row.classList.remove('d-none');
            }

        }
    })
    

});