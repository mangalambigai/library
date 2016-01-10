from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Book(Base):
    __tablename__='book'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    author = Column(String(250), nullable = False)
    subject = Column(String(20), nullable = False)
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name' : self.name,
           'id' : self.id,
           'author' : self.author,
           'subject' : self.subject,
       }

class Student(Base):
    __tablename__='student'

    id = Column(Integer, primary_key = True)
    name = Column(String(40), nullable = False)
    email = Column(String(50), nullable = True)
    cellphone = Column(String(10), nullable = True)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id' : self.id,
            'name' : self.name,
            'email' : self.email,
            'cellphone' : self.cellphone,
        }

class Checkout(Base):
    __tablename__='checkout'
    id = Column(Integer, primary_key = True)
    student_id = Column(Integer, ForeignKey('student.id'))
    book_id = Column(Integer, ForeignKey('book.id'))
    checkout_date = Column(Date)
    due_date = Column(Date)
    librarian_id = Column(String(50))
    book = relationship(Book)
    student = relationship(Student)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id' : self.id,
            'student_id' : self.student_id,
            'book_id' : self.book_id,
            'due_date' : self.due_date,
        }

engine = create_engine('sqlite:///library.db')

Base.metadata.create_all(engine)


