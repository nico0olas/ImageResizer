import os
import threading
import time
import uuid
from pathlib import Path
from PIL import Image


from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.views.generic.edit import FormView

from .forms import FileFieldForm

DELAY = 16  # delay in seconds before deleting file
MAX_IMG = 8 # max number of images to resize

# reduce size of image

def reduce_size_image(img_path: str, compression: int) :
    """
    Reduce size of image
    """
    img = Image.open(img_path)
    
    # Apres un vérfication de l'image, on doit la réouvrir
    # https://pillow.readthedocs.io/en/latest/reference/Image.html#PIL.Image.Image.verify
    
    img.verify()
    img = Image.open(img_path)

    new_img = img.reduce(int(compression))
    new_img.save(img_path)

    return None

def custom_404_view(request, exception):
    """ return 404 page """
    return render(request, 'ImgResize/404.html', status=404)

def delete_file_after_delay(delay, file_to_delete):
    """ delete file after delay """
    time.sleep(delay)
    for file in file_to_delete:
        os.remove(file)

def result(request, img):
    """ return result page """
    return render(request, 'ImgResize/result.html', context={'img': img})

#https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/
class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "ImgResize/index.html"  
    success_url = "http://127.0.0.1:8000/"  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delay"] = DELAY
        context["max_img"] = MAX_IMG
        return context
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        context = {}
        files_to_delete = []
        if len(files) > MAX_IMG:
            return render(self.request, 'ImgResize/index.html', context={'form': form, 'err': '5 images maximum !'})
        for f in files:
            # on transforme le nom du fichier en uuid pour éviter les collisions
            random_uuid = str(uuid.uuid4())
            # on utilise filesystemstorage pour stocker le fichier sans passer par la base de données
            fs = FileSystemStorage()
            
            # on récupère l'extension du fichier pour la réutiliser
            ext = Path(f.name).suffix
            filename = fs.save(f"{random_uuid}{ext}", f)
            files_to_delete.append(f"{fs.location}/{filename}")
            try:
                reduce_size_image(f"{fs.location}/{filename}", form.cleaned_data["compression"] )
            except Exception as err: 
                print("error",err)
                # en cas d'erreur on supprime le fichier immediatement quelques soit l'erreur et on affiche un message d'erreur
                delete_file_after_delay(0, files_to_delete)
                return render(self.request, 'ImgResize/index.html', context={'form': form, 'err': 'Le fichier suivant ne semble pas etre une image : <br><br> ' + f.name})
            uploaded_file_url = fs.url(filename)
            # on stocke les informations dans un dictionnaire pour les réutiliser dans le template
            context[random_uuid] =  {'url': uploaded_file_url, 'name': f.name }

        # on lance un thread pour supprimer les fichiers après un délai de 10 secondes
        deletion_thread = threading.Thread(target=delete_file_after_delay, args=([DELAY, files_to_delete]))
        deletion_thread.start()

        return render(self.request,  'ImgResize/result.html', context={"result": context, "delay": DELAY})
    
    