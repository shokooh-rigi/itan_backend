import os
import zipfile

from mysite.s3_file_manager import S3


class BidFileService:
    @staticmethod
    def handle_uploaded_files(files_list, temp_path):
        """
        Saves each uploaded file to the specified temporary path and returns a list of their paths.
        """
        file_paths = []
        for f in files_list:
            file_path = os.path.join(temp_path, f.name)
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            file_paths.append(file_path)
        return file_paths

    @staticmethod
    def create_zip_file(filenames, path, project_name):
        """
        Creates a zip file from the provided file paths and returns the zip file path.
        """
        # Ensure the zip filename has a .zip extension
        zip_filename = os.path.join(path, f"{project_name}.zip")
        
        # Create a new zip file
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in filenames:
                fdir, fname = os.path.split(file)
                zf.write(file, fname)  # Store the file in the zip
                os.remove(file)  # Remove the original file after adding it to the zip

        return zip_filename

    @staticmethod
    def clean_project_name(project_name):
        """
        Cleans special characters from project names for safe file naming.
        """
        return project_name.replace(' ', '_') \
            .replace('!', '').replace('@', '').replace('#', '').replace('$', '') \
            .replace('%', '').replace('^', '').replace('&', '').replace('*', '').replace("/", '')

    @staticmethod
    def update_bidfile_with_zip(bidfile, zip_file_path):
        print(zip_file_path)
        """
        Uploads the zip file to S3 and updates the bidfile record with the file path.
        """
        s3 = S3()
        with open(zip_file_path, 'rb') as file:
            bidfile.uploaded_file.save(os.path.basename(zip_file_path), file)
        os.remove(zip_file_path)  # Cleanup zip file after upload
