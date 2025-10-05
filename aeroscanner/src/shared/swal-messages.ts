// error an success message
import Swal from "sweetalert2";

export class SwalMessages{

    // shows succes message
    successMessage(message: string){
        Swal.fire({
            position: 'top-end',
            icon: 'success',
            toast: true,
            text: message,
            background: '#E8F8F8',
            showConfirmButton: false,
            timer: 2000
        });
    }

    // shows error message
    errorMessage(message: string){
        Swal.fire({
            position: 'top-end',
            icon: 'error',
            toast: true,
            text: message,
            background: '#F8E8F8',
            showConfirmButton: false,
            timer: 2000
        });
    }

    // shows confirmation message
    confirmMessage = Swal.mixin({
        icon: 'warning',
        showCancelButton: true,
        cancelButtonText: `Cancelar`,
        confirmButtonText: "Confirmar",
        customClass: {
            title: 'swal-title',
            icon: 'swal-icon',
            confirmButton: 'btn noneb btn-success swal-confirm-button',
            cancelButton: 'btn  noneb btn-danger swal-cancel-button',
        },
    });
}
