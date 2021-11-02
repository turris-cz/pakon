class Objson:  # json -> object
    """Dict structure to object attributes"""
    def __init__(self, __data) -> None:
        self.__dict__= {
            key: Objson(val) if isinstance(val,dict)
            else val for key, val in __data.items()
        }

    def __repr__(self) -> str:
        return str(self.__dict__)
