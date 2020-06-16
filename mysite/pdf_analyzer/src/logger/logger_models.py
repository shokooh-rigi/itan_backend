ADDRESS_RUN_STEPS = [
    'Converting PDF to image',
    'Detecting text boxes in image',
    'Converting to text',
    'Calculating similarity of lines to the project name',
    'Finding project address'
]


class AddressRunSteps:
    PDFToImage = 1
    DetectingBoxes = 2
    ConvertingToText = 3
    CalculatingSimilarity = 4
    FindingAddress = 5
