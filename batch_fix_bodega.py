import re
import os

def fix_file(file_path):
    print(f"Processing {file_path}...")
    if not os.path.exists(file_path):
        print(f"Skip: {file_path} not found")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Join split lines for badge span
    span_pattern = r'<span\s+class="badge {% if articulo\.stock_actual > articulo\.stock_minimo %\}bg-success\{% elif articulo\.stock_actual > 0 %\}bg-warning\{% else %\}bg-danger\{% endif %}\">[\s\n\r]*\{\{\s*articulo\.stock_actual\|default:0\s*\}\}\s*\{\{[\s\n\r]*articulo\.unidad_medida\.simbolo\|default:"unidad"\s*\}\}[\s\n\r]*</span>'
    content = re.sub(span_pattern, 
                     '<span class="badge {% if articulo.stock_actual > articulo.stock_minimo %}bg-success{% elif articulo.stock_actual > 0 %}bg-warning{% else %}bg-danger{% endif %}">{{ articulo.stock_actual|default:0 }} {{ articulo.unidad_medida.simbolo|default:"unidad" }}</span>', 
                     content, flags=re.DOTALL)

    # 2. Join split lines for disabled button condition
    btn_pattern = r'<button type="button" class="btn btn-sm btn-success btn-seleccionar-articulo" {% if[\s\n\r]*articulo\.stock_actual\s*<=\s*0\s*%\}disabled\{% endif %\}>'
    content = re.sub(btn_pattern, 
                     '<button type="button" class="btn btn-sm btn-success btn-seleccionar-articulo" {% if articulo.stock_actual <= 0 %}disabled{% endif %}>', 
                     content, flags=re.DOTALL)

    # 3. Handle more general split tags that might break things
    content = re.sub(r'\{%[ \t\r\n]+', '{% ', content)
    content = re.sub(r'[ \t\r\n]+%\}', ' %}', content)

    # 4. Remove the inline Python array script at the end and replace with static init
    # We look for a script block that contains {% for articulo in articulos %}
    script_pattern = r'<script>[\s\n\r]*\(function\s*\(\)\s*\{[\s\n\r]*const\s+articulos\s*=\s*\[[\s\n\r]*\{% for articulo in articulos %\}.*?init\(articulos\);.*?\}\s*\)\s*\(\);[\s\n\r]*</script>'
    new_script = """<script>
    (function() {
        if (window.EntregaArticulos) {
            window.EntregaArticulos.init();
        } else {
            console.error('EntregaArticulos no está definido');
        }
    })();
</script>"""
    
    # Check if the script exists before replacing
    if '{% for articulo in articulos %}' in content:
        content = re.sub(script_pattern, new_script, content, flags=re.DOTALL)

    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("Done.")

if __name__ == "__main__":
    files = [
        r'c:\proyectos\tba\templates\bodega\entrega_articulo\form.html',
        r'c:\proyectos\tba\templates\bodega\entrega_bien\form.html',
        r'c:\proyectos\tba\templates\bodega\entrega_bien\modal_form.html',
        r'c:\proyectos\tba\templates\bodega\recepcion_activo\form.html',
        r'c:\proyectos\tba\templates\bodega\recepcion_activo\modal_form.html',
        r'c:\proyectos\tba\templates\bodega\recepcion_articulo\form.html',
        r'c:\proyectos\tba\templates\bodega\recepcion_articulo\modal_form.html',
    ]
    for f in files:
        fix_file(f)
